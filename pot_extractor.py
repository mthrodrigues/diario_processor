import re


# Faixas horizontais aproximadas das colunas da tabela POT.
# Baseadas na geometria observada no PDF diario_3252.pdf.
COLUNAS_POT = {
    "beneficiario": (85, 178),
    "unidade": (190, 265),
    "area_aprendizado": (270, 370),
    "data_inclusao": (375, 445),
    "substituicao": (448, 535),
}


PADRAO_CABECALHO_POT = re.compile(
    r"BENEFICI[ÁA]RIOS\s+DO\s+PROGRAMA\s+OPERA[ÇC][ÃA]O\s+TRABALHO\s*\(POT\)",
    flags=re.IGNORECASE,
)

PADRAO_DATA = re.compile(r"\b\d{2}/\d{2}/\d{4}\b")

PADRAO_DESLIGAMENTO = re.compile(
    r"\(\s*desligad[ao]\s+em\s+\d{2}/\d{2}/\d{4}\s*\)",
    flags=re.IGNORECASE,
)


def _normalizar_texto(valor):
    """Normaliza espaços sem alterar o conteúdo textual."""
    if not valor:
        return None

    valor = re.sub(r"\s+", " ", valor).strip()

    return valor or None


def _extrair_texto_coluna(palavras, x_min, x_max):
    """
    Extrai palavras pertencentes a uma coluna e preserva
    a ordem vertical/horizontal da célula.
    """
    selecionadas = []

    for palavra in palavras:
        x0 = palavra["x0"]
        x1 = palavra["x1"]

        # Considera a palavra pertencente à coluna quando
        # há sobreposição horizontal com a faixa da coluna.
        if x1 >= x_min and x0 <= x_max:
            selecionadas.append(palavra)

    # Ordem de leitura dentro da célula.
    selecionadas.sort(key=lambda p: (p["top"], p["x0"]))

    return _normalizar_texto(
        " ".join(p["text"] for p in selecionadas)
    )


def _remover_rodape_autenticidade(palavras):
    """
    Remove palavras pertencentes ao rodapé de autenticação
    digital do Diário Oficial.
    """
    resultado = []

    for palavra in palavras:
        texto = palavra["text"].lower()
        top = palavra["top"]

        # O rodapé começa aproximadamente em y=760 nesta página.
        if top >= 755:
            continue

        if "autenticidade" in texto:
            continue

        if "digitalmente" in texto:
            continue

        resultado.append(palavra)

    return resultado


def _encontrar_inicio_registros(palavras):
    """
    Localiza os números da coluna Nº que iniciam registros POT.

    O número deve estar:
      - na faixa horizontal da coluna Nº;
      - associado a texto efetivamente pertencente à tabela POT.

    Retorna uma lista de:
        (numero, top)
    """
    inicios = []

    for palavra in palavras:
        texto = palavra["text"].strip()

        if not texto.isdigit():
            continue

        x0 = palavra["x0"]
        x1 = palavra["x1"]
        top = palavra["top"]

        # Coluna Nº.
        if not (60 <= x0 <= 82 and x1 <= 85):
            continue

        numero = int(texto)

        if numero <= 0 or numero > 100:
            continue

        inicios.append((numero, top))

    inicios.sort(key=lambda item: item[1])

    return inicios

def _extrair_palavras_registro(pagina, bbox):
    """
    Extrai palavras dentro do bbox de uma linha da tabela,
    preservando a posição espacial.
    """
    palavras = pagina.crop(bbox).extract_words(
        x_tolerance=3,
        y_tolerance=3,
        keep_blank_chars=False,
    )

    return sorted(
        palavras,
        key=lambda p: (p["top"], p["x0"]),
    )


def _extrair_registro_por_coordenadas(pagina, bbox):
    """
    Reconstrói um registro POT a partir das posições X das palavras.

    Usado somente quando a extração estrutural da tabela deixa
    uma linha incompleta.
    """
    palavras = _extrair_palavras_registro(pagina, bbox)

    campos = {
        "beneficiario": [],
        "unidade": [],
        "area_aprendizado": [],
        "data_inclusao": [],
        "substituicao": [],
    }

    for palavra in palavras:
        x0 = palavra["x0"]
        texto = palavra["text"]

        if 85 <= x0 < 190:
            campo = "beneficiario"
        elif 190 <= x0 < 270:
            campo = "unidade"
        elif 270 <= x0 < 375:
            campo = "area_aprendizado"
        elif 375 <= x0 < 448:
            campo = "data_inclusao"
        elif 448 <= x0 <= 540:
            campo = "substituicao"
        else:
            continue

        campos[campo].append(texto)

    return {
        campo: _normalizar_texto(" ".join(valores))
        for campo, valores in campos.items()
    }

def _combinar_registros_pot(registro_anterior, continuacao):
    """
    Combina dois fragmentos que representam a mesma linha lógica
    da tabela POT, atravessando uma quebra de página.

    O registro anterior tem prioridade nos campos já preenchidos.
    Quando ambos os fragmentos possuem conteúdo no mesmo campo,
    os textos são concatenados preservando a ordem documental.
    """

    campos = (
        "beneficiario",
        "unidade",
        "horario_atuacao",
        "area_aprendizado",
        "data_inclusao",
        "data_desligamento",
        "substituicao",
    )

    combinado = {
        "numero": (
            continuacao["numero"]
            if continuacao.get("numero") is not None
            else registro_anterior.get("numero")
        ),
    }

    for campo in campos:
        valor_anterior = registro_anterior.get(campo)
        valor_continuacao = continuacao.get(campo)

        if valor_anterior and valor_continuacao:
            combinado[campo] = _normalizar_texto(
                f"{valor_anterior} {valor_continuacao}"
            )
        else:
            combinado[campo] = (
                valor_anterior
                or valor_continuacao
                or None
            )

    combinado["texto_bruto"] = _normalizar_texto(
        " ".join(
                valor
                for valor in (
                    combinado["beneficiario"],
                    combinado["unidade"],
                    combinado["horario_atuacao"],
                    combinado["area_aprendizado"],
                    combinado["data_inclusao"],
                    combinado["data_desligamento"],
                    combinado["substituicao"],
                )
            if valor
        )
    )

    return combinado

def _corrigir_numero_e_beneficiario_pot(
    numero_raw,
    beneficiario_raw,
):
    """
    Corrige contaminação da coluna Nº por fragmentos da coluna
    Beneficiário(s), observada em determinados PDFs.

    Exemplos reais:
        "I\\n3"   + "ngrid Dias de\\nOliveira"
        "S\\n1\\nd" + "amanta Pires\\ne Almeida"
        "2 J"     + "Mariane de\\nesús da Silva\\nCandido"

    O número é extraído do trecho numérico da célula Nº.
    Fragmentos alfabéticos são reinseridos apenas nas linhas do
    beneficiário que começam em minúscula.
    """

    if not numero_raw:
        return None, beneficiario_raw

    numero_raw = numero_raw.strip()

    match = re.search(r"\d+", numero_raw)

    if not match:
        return numero_raw, beneficiario_raw

    numero = match.group(0)

    fragmentos = re.findall(
        r"[A-Za-zÀ-ÖØ-öø-ÿ]",
        numero_raw[:match.start()] +
        numero_raw[match.end():],
    )

    if not fragmentos or not beneficiario_raw:
        return numero, beneficiario_raw

    linhas = beneficiario_raw.splitlines()

    indices_linhas_fragmentadas = [
        i
        for i, linha in enumerate(linhas)
        if linha.strip()
        and linha.strip()[0].islower()
    ]

    if len(fragmentos) > len(indices_linhas_fragmentadas):
        return numero, beneficiario_raw

    for fragmento, indice in zip(
        fragmentos,
        indices_linhas_fragmentadas,
    ):
        linhas[indice] = (
            fragmento + linhas[indice]
        )

    beneficiario = _normalizar_texto(
        " ".join(linhas)
    )

    return numero, beneficiario

def _registro_pot_da_linha(linha, layout):
    """
    Converte uma linha de tabela POT em um registro lógico.

    layout:
        "ativo"
        "desligado"
    """

    numero, beneficiario = (
        _corrigir_numero_e_beneficiario_pot(
            linha[0],
            linha[1],
        )
    )

    registro = {
        "numero": numero,
        "beneficiario": beneficiario.strip()
        if beneficiario
        else None,
        "unidade": (
            linha[2].strip()
            if linha[2]
            else None
        ),
        "horario_atuacao": None,
        "area_aprendizado": None,
        "data_inclusao": None,
        "data_desligamento": None,
        "substituicao": None,
    }

    if layout == "ativo":
        registro["area_aprendizado"] = (
            linha[3].strip()
            if linha[3]
            else None
        )

        registro["data_inclusao"] = (
            linha[4].strip()
            if linha[4]
            else None
        )

        registro["substituicao"] = (
            linha[5].strip()
            if linha[5]
            else None
        )

    elif layout == "desligado":
        registro["horario_atuacao"] = (
            linha[3].strip()
            if linha[3]
            else None
        )

        registro["area_aprendizado"] = (
            linha[4].strip()
            if linha[4]
            else None
        )

        registro["data_desligamento"] = (
            linha[5].strip()
            if linha[5]
            else None
        )

    else:
        raise ValueError(
            f"Layout POT desconhecido: {layout}"
        )

    registro["texto_bruto"] = " ".join(
        valor
        for chave, valor in registro.items()
        if chave not in {
            "texto_bruto",
        }
        and valor
    )

    return registro

def _recuperar_numero_pot_por_coordenadas(
    pagina,
    bbox,
):
    """
    Recupera o número da primeira linha de uma tabela POT quando
    a coluna Nº ficou fora do bbox detectado pelo pdfplumber.

    Considera somente a faixa horizontal imediatamente à esquerda
    da tabela e a altura da primeira linha de dados.
    """

    palavras = pagina.extract_words(
        x_tolerance=3,
        y_tolerance=3,
        keep_blank_chars=False,
    )

    x_min, y_min, _, _ = bbox

    candidatos = []

    for palavra in palavras:
        texto = palavra["text"].strip()

        if not texto.isdigit():
            continue

        if not (x_min - 30 <= palavra["x0"] < x_min):
            continue

        if palavra["top"] < y_min:
            continue

        candidatos.append(palavra)

    if not candidatos:
        return None

    candidatos.sort(
        key=lambda p: (p["top"], p["x0"])
    )

    return candidatos[0]["text"]

def _corrigir_coluna_numero_ausente_pot(dados):
    """
    Corrige tabelas POT nas quais o pdfplumber não detecta
    a primeira coluna física (Nº), deslocando as demais colunas
    uma posição para a esquerda.

    Nessa variante, o cabeçalho começa por "Beneficiário(s)",
    indicando que a coluna Nº foi perdida.
    """

    if not dados:
        return dados

    primeira_linha = dados[0]

    if len(primeira_linha) != 5:
        return dados

    cabecalho = " ".join(
        celula.strip()
        for celula in primeira_linha
        if celula and celula.strip()
    ).upper()

    if (
        "BENEFICIÁRIO" not in cabecalho
        and "BENEFICIARIO" not in cabecalho
    ):
        return dados

    corrigidos = []

    for linha in dados:
        linha = list(linha)

        while len(linha) < 5:
            linha.append("")

        corrigidos.append(
            [""] + linha
        )

    return corrigidos

def _extrair_registros_pot_tabela(
    dados,
    numero_inicial=None,
):
    """
    Extrai os registros físicos de uma tabela POT isolada.

    Não faz reconstrução entre páginas.
    """

    dados = _corrigir_coluna_numero_ausente_pot(dados)

    if (
        numero_inicial is not None
        and len(dados) > 1
        and not dados[1][0]
    ):
        dados[1][0] = numero_inicial

    layout = _identificar_layout_tabela_pot(dados)

    if layout is None:
        return []

    indice_cabecalho = _localizar_cabecalho_pot(dados)

    if indice_cabecalho is None:
        return []

    registros = []

    for linha in dados[indice_cabecalho + 1:]:
        if not linha:
            continue

        if not any(
            celula and celula.strip()
            for celula in linha
        ):
            continue

        linha = list(linha)

        while len(linha) < 6:
            linha.append("")

        registro = _registro_pot_da_linha(
            linha,
            layout,
        )

        if not any(
            registro.get(campo)
            for campo in (
                "numero",
                "beneficiario",
                "unidade",
                "horario_atuacao",
                "area_aprendizado",
                "data_inclusao",
                "data_desligamento",
                "substituicao",
            )
        ):
            continue

        registros.append(registro)

    return registros

def _agrupar_publicacoes_pot(pdf):
    """
    Agrupa tabelas físicas POT em publicações POT lógicas.

    Cada grupo corresponde a uma publicação POT e preserva a
    estrutura física das tabelas que a compõem.

    Uma nova publicação começa quando a numeração reinicia em 1.

    Retorno:

        [
            [
                {
                    "pagina": 5,
                    "tabela": 1,
                    "layout": "ativo",
                    "registros": [...],
                },
                {
                    "pagina": 6,
                    "tabela": 0,
                    "layout": "ativo",
                    "registros": [...],
                },
                ...
            ],
            ...
        ]
    """

    grupos = []
    grupo_atual = []
    fragmento_pendente = None

    for pagina_numero, pagina in enumerate(
        pdf.pages,
        start=1,
    ):

        for tabela_numero, tabela in enumerate(
            pagina.find_tables()
        ):
            dados = tabela.extract()

            if not dados:
                continue

            layout = _identificar_layout_tabela_pot(dados)

            if layout is None:
                continue

            numero_inicial = None

            if len(dados) >= 2:
                numero_inicial = _recuperar_numero_pot_por_coordenadas(
                    pagina,
                    tabela.bbox,
                )

            registros = _extrair_registros_pot_tabela(
                dados,
                numero_inicial=numero_inicial,
            )

            if not registros:
                continue

            numeros = []

            for registro in registros:
                numero = registro.get("numero")

                if numero is None:
                    continue

                try:
                    numeros.append(int(numero))
                except (TypeError, ValueError):
                    continue

            primeiro_numero = (
                numeros[0]
                if numeros
                else None
            )

            tabela_atual = {
                "pagina": pagina_numero,
                "tabela": tabela_numero,
                "layout": layout,
                "registros": registros,
            }

            # -------------------------------------------------
            # Tabela composta exclusivamente por registros
            # sem número.
            #
            # Ela pode ser:
            #
            # 1. continuação do grupo atual; ou
            # 2. início fragmentado de uma nova publicação,
            #    caso a próxima tabela POT comece em 1.
            #
            # Mantemos a tabela pendente até conhecer a
            # próxima tabela POT.
            # -------------------------------------------------
            if (
                registros
                and all(
                    registro.get("numero") is None
                    for registro in registros
                )
            ):
                fragmento_pendente = tabela_atual
                continue

            # -------------------------------------------------
            # Resolve fragmento POT pendente.
            # -------------------------------------------------
            nova_publicacao_por_fragmento = False

            if fragmento_pendente is not None:
                if primeiro_numero == 1:
                    if grupo_atual:
                        grupos.append(grupo_atual)

                    grupo_atual = [
                        fragmento_pendente
                    ]

                    nova_publicacao_por_fragmento = True

                else:
                    grupo_atual.append(
                        fragmento_pendente
                    )

                fragmento_pendente = None

            # -------------------------------------------------
            # Nova publicação POT convencional:
            #
            # a numeração reiniciou em 1.
            # -------------------------------------------------
            if (
                not nova_publicacao_por_fragmento
                and grupo_atual
                and primeiro_numero == 1
            ):
                grupos.append(grupo_atual)
                grupo_atual = []

            grupo_atual.append(tabela_atual)

    if fragmento_pendente is not None:
        grupo_atual.append(fragmento_pendente)

    if grupo_atual:
        grupos.append(grupo_atual)

    return grupos

def _reconstruir_publicacoes_pot(grupos_fisicos):
    """
    Reconstrói os registros lógicos de cada publicação POT a partir
    das tabelas físicas agrupadas.

    A reconstrução respeita as fronteiras entre tabelas físicas e
    reproduz os dois padrões reais de continuação:

    1. A nova tabela começa com fragmento sem número e a segunda
       linha é N+1.
    2. A tabela anterior termina com fragmento sem número e a nova
       tabela começa diretamente com N+1.

    Retorna uma lista de grupos lógicos, um por publicação POT.
    """

    publicacoes = []

    for grupo in grupos_fisicos:
        registros_finais = []

        ultimo_registro_tabela = None
        ultimo_numero_tabela = None

        for tabela in grupo:
            registros = list(
                tabela.get("registros", [])
            )
            if (
                ultimo_registro_tabela is not None
                and ultimo_registro_tabela.get("numero") is not None
                and registros
                and all(
                    registro.get("numero") is None
                    for registro in registros
                )
            ):
                combinado = _combinar_registros_pot(
                    registros_finais[-1],
                    registros[0],
                )

                registros_finais[-1] = combinado
                ultimo_registro_tabela = combinado

                continue

            if not registros:
                continue

            primeiro = registros[0]

            primeiro_numero = None

            if primeiro.get("numero") is not None:
                try:
                    primeiro_numero = int(
                        primeiro["numero"]
                    )
                except (TypeError, ValueError):
                    primeiro_numero = None

            # =====================================================
            # PADRÃO 2
            #
            # A tabela anterior termina com um fragmento sem
            # número e a nova tabela começa novamente em 1.
            #
            # Ex.: "Eni Reis Jardim" + "1 Sobrinho"
            #      -> "Eni Reis Jardim Sobrinho"
            # =====================================================

            if (
                ultimo_registro_tabela is not None
                and ultimo_registro_tabela.get("numero") is None
                and primeiro_numero == 1
            ):
                combinado = _combinar_registros_pot(
                    ultimo_registro_tabela,
                    primeiro,
                )

                registros_finais[-1] = combinado
                registros = registros[1:]

            # =====================================================
            # PADRÃO 3
            #
            # A tabela atual começa com N+1 e o último registro
            # da tabela anterior era um fragmento sem número.
            # =====================================================

            if (
                ultimo_registro_tabela is not None
                and ultimo_registro_tabela.get("numero") is None
                and primeiro_numero is not None
                and ultimo_numero_tabela is not None
                and primeiro_numero
                == ultimo_numero_tabela + 1
            ):
                combinado = _combinar_registros_pot(
                    ultimo_registro_tabela,
                    primeiro,
                )

                registros_finais[-1] = combinado

                registros = registros[1:]

            # =====================================================
            # PADRÃO 1
            #
            # A tabela atual começa com fragmento sem número e
            # a segunda linha é N+1.
            # =====================================================

            elif (
                ultimo_registro_tabela is not None
                and ultimo_registro_tabela.get("numero") is not None
                and primeiro_numero is None
                and ultimo_numero_tabela is not None
                and len(registros) >= 2
            ):
                segundo = registros[1]

                segundo_numero = None

                if segundo.get("numero") is not None:
                    try:
                        segundo_numero = int(
                            segundo["numero"]
                        )
                    except (TypeError, ValueError):
                        segundo_numero = None

                if (
                    segundo_numero is not None
                    and segundo_numero
                    == ultimo_numero_tabela + 1
                ):
                    fragmento = registros[0]

                    combinado = _combinar_registros_pot(
                        registros_finais[-1],
                        fragmento,
                    )

                    registros_finais[-1] = combinado

                    registros = registros[1:]

            # =====================================================
            # Registros restantes da tabela atual
            # =====================================================

            registros_finais.extend(registros)

            # =====================================================
            # Atualiza o estado da tabela atual.
            # =====================================================

            ultimo_registro_tabela = (
                registros[-1]
                if registros
                else ultimo_registro_tabela
            )

            numeros_restantes = []

            for registro in registros:
                numero = registro.get("numero")

                if numero is None:
                    continue

                try:
                    numeros_restantes.append(
                        int(numero)
                    )
                except (TypeError, ValueError):
                    continue

            if numeros_restantes:
                ultimo_numero_tabela = max(
                    numeros_restantes
                )

        publicacoes.append(
            registros_finais
        )

    return publicacoes

def extrair_publicacoes_pot_pdf(pdf):
    """
    Extrai as publicações POT agrupadas por ocorrência documental.

    Retorna uma lista em ordem documental, contendo uma lista de
    registros lógicos para cada publicação POT.
    """

    grupos_fisicos = _agrupar_publicacoes_pot(pdf)

    return _reconstruir_publicacoes_pot(
        grupos_fisicos
    )

def extrair_registros_pot_pdf(pdf):
    """
    Extrai os registros POT de um PDF completo, reconstruindo
    registros cuja linha atravessa a quebra de página.

    A continuidade é avaliada entre a última tabela POT de uma
    página e a primeira tabela POT da página seguinte.

    Há dois padrões observados no layout real do Diário:

    1. A página seguinte começa com uma linha sem número,
       continuação do último registro da página anterior.

       Exemplo:
           página N:
               40 | ...
           página N+1:
                  | continuação...
               41 | ...

    2. A página anterior termina com uma linha sem número,
       e a página seguinte começa com o número do registro
       que estava em continuação.

       Exemplo:
           página N:
                  | fragmento...
           página N+1:
               4 | continuação...
               5 | ...

    A sequência numérica é calculada dentro da tabela POT,
    nunca sobre todas as tabelas da página.
    """

    registros_finais = []

    # Último número explícito processado dentro da tabela POT
    # que terminou a iteração anterior.
    ultimo_numero_tabela = None

    # Último registro da tabela POT anterior.
    ultimo_registro_tabela = None

    for pagina in pdf.pages:
        tabelas_pot = []

        for tabela in pagina.find_tables():
            dados = tabela.extract()

            if not dados:
                continue

            if not _eh_tabela_pot(dados):
                continue

            tabelas_pot.append(
                (tabela, dados)
            )

        if not tabelas_pot:
            continue

        for _, dados in tabelas_pot:
            layout = _identificar_layout_tabela_pot(dados)

            if layout is None:
                continue

            indice_cabecalho = _localizar_cabecalho_pot(dados)

            if indice_cabecalho is None:
                continue

            linhas = [
                linha
                for linha in dados[indice_cabecalho + 1:]
                if linha
                and any(
                    celula and celula.strip()
                    for celula in linha
                )
            ]

            if not linhas:
                continue

            # -----------------------------------------------------
            # Estado da tabela atual.
            # -----------------------------------------------------
            primeiro = linhas[0]

            numeros_tabela = []

            for linha in linhas:
                numero = linha[0]

                if not numero:
                    continue

                try:
                    numeros_tabela.append(
                        int(numero)
                    )
                except (TypeError, ValueError):
                    continue

            primeiro_numero = None

            if primeiro[0]:
                try:
                    primeiro_numero = int(
                        primeiro[0]
                    )
                except (TypeError, ValueError):
                    primeiro_numero = None

            # -----------------------------------------------------
            # PADRÃO 2
            #
            # Último registro da tabela anterior era um fragmento
            # sem número e a tabela atual começa com N+1.
            # -----------------------------------------------------
            if (
                ultimo_registro_tabela is not None
                and ultimo_registro_tabela.get("numero") is None
                and primeiro_numero is not None
                and ultimo_numero_tabela is not None
                and primeiro_numero
                == ultimo_numero_tabela + 1
            ):
                registro_completo = _combinar_registros_pot(
                    ultimo_registro_tabela,
                    _registro_pot_da_linha(
                        primeiro,
                        layout,
                    )
                )

                registros_finais[-1] = registro_completo

                linhas = linhas[1:]

            # -----------------------------------------------------
            # PADRÃO 1
            #
            # O último registro da tabela anterior tinha número N.
            # A primeira linha da tabela atual é um fragmento sem
            # número. A linha numerada seguinte deve ser N+1.
            # -----------------------------------------------------
            elif (
                ultimo_registro_tabela is not None
                and ultimo_registro_tabela.get("numero")
                is not None
                and not primeiro_numero
                and ultimo_numero_tabela is not None
                and len(linhas) >= 2
            ):
                segundo = linhas[1]

                segundo_numero = None

                if segundo[0]:
                    try:
                        segundo_numero = int(
                            segundo[0]
                        )
                    except (TypeError, ValueError):
                        segundo_numero = None

                if (
                    segundo_numero is not None
                    and segundo_numero
                    == ultimo_numero_tabela + 1
                ):
                    fragmento = _registro_pot_da_linha(
                        primeiro,
                        layout,
                    )

                    registro_base = (
                        registros_finais[-1]
                    )

                    registros_finais[-1] = _combinar_registros_pot(
                        registro_base,
                        fragmento,
                    )

                    linhas = linhas[1:]

            # -----------------------------------------------------
            # Registra as linhas restantes da tabela atual.
            # -----------------------------------------------------
            registros_tabela = [
                _registro_pot_da_linha(
                    linha,
                    layout,
                )
                for linha in linhas
            ]

            registros_finais.extend(
                registros_tabela
            )

            # -----------------------------------------------------
            # Atualiza o estado APENAS com esta tabela.
            # -----------------------------------------------------
            ultimo_registro_tabela = (
                registros_tabela[-1]
                if registros_tabela
                else ultimo_registro_tabela
            )

            numeros_restantes = []

            for registro in registros_tabela:
                numero = registro.get("numero")

                if numero is None:
                    continue

                try:
                    numeros_restantes.append(
                        int(numero)
                    )
                except (TypeError, ValueError):
                    continue

            if numeros_restantes:
                ultimo_numero_tabela = max(
                    numeros_restantes
                )

    return registros_finais

def _localizar_cabecalho_pot(dados):
    """
    Localiza a linha que contém o cabeçalho estrutural de uma
    tabela POT.

    O cabeçalho pode ocupar a primeira ou uma das primeiras
    linhas da tabela. Quando o PDF fragmenta o cabeçalho em
    linhas físicas consecutivas, elas são analisadas em conjunto.
    """

    if not dados:
        return None

    limite = min(len(dados), 5)

    for indice in range(limite):

        linha = dados[indice]

        if not linha:
            continue

        texto = " ".join(
            celula.strip()
            for celula in linha
            if celula and celula.strip()
        )

        texto_upper = texto.upper()

        if (
            (
                "BENEFICIÁRIO" in texto_upper
                or "BENEFICIARIO" in texto_upper
            )
            and (
                "ATUAÇÃO" in texto_upper
                or "ATUACAO" in texto_upper
                or "TRABALHO" in texto_upper
            )
            and "APRENDIZADO" in texto_upper
        ):
            return indice

        if indice + 1 >= limite:
            continue

        proxima_linha = dados[indice + 1]

        if not proxima_linha:
            continue

        texto_combinado = " ".join(
            celula.strip()
            for linha_cabecalho in (
                linha,
                proxima_linha,
            )
            for celula in linha_cabecalho
            if celula and celula.strip()
        )

        texto_combinado_upper = texto_combinado.upper()

        if (
            (
                "BENEFICIÁRIO" in texto_combinado_upper
                or "BENEFICIARIO" in texto_combinado_upper
            )
            and (
                "ATUAÇÃO" in texto_combinado_upper
                or "ATUACAO" in texto_combinado_upper
                or "TRABALHO" in texto_combinado_upper
            )
            and "APRENDIZADO" in texto_combinado_upper
        ):
            return indice + 1

    return None


def _identificar_layout_tabela_pot(dados):
    """
    Identifica a variante documental da tabela POT.

    Retorna:
        "ativo"
        "desligado"
        None
    """

    indice_cabecalho = _localizar_cabecalho_pot(dados)

    if indice_cabecalho is None:
        return None

    linhas_cabecalho = [
        dados[indice_cabecalho],
    ]

    if indice_cabecalho > 0:
        linha_anterior = dados[indice_cabecalho - 1]

        texto_atual = " ".join(
            celula.strip()
            for celula in dados[indice_cabecalho]
            if celula and celula.strip()
        ).upper()

        if (
            "DATA DE DESLIGAMENTO" not in texto_atual
            and "DATA DA INCLUSÃO" not in texto_atual
            and "DATA DA INCLUSAO" not in texto_atual
        ):
            linhas_cabecalho.insert(
                0,
                linha_anterior,
            )

    cabecalho = re.sub(
        r"\s+",
        " ",
        " ".join(
            celula.strip()
            for linha in linhas_cabecalho
            for celula in linha
            if celula and celula.strip()
        ),
    ).upper()

    if (
        "DATA" in cabecalho
        and "DESLIGAMENTO" in cabecalho
    ):
        return "desligado"

    if (
        (
            "DATA DA INCLUSÃO" in cabecalho
            or "DATA DA INCLUSAO" in cabecalho
        )
        and (
            "EM SUBSTITUIÇÃO" in cabecalho
            or "EM SUBSTITUICAO" in cabecalho
        )
    ):
        return "ativo"

    return None


def _eh_tabela_pot(dados):
    """
    Verifica se uma tabela possui estrutura documental POT
    reconhecida.
    """

    return _identificar_layout_tabela_pot(dados) is not None

def _extrair_registros_pot_pagina(pagina):
    """
    Extrai registros POT de todas as tabelas POT encontradas
    em uma única página.

    Suporta as variantes:
        - beneficiários ativos;
        - beneficiários desligados.

    A reconstrução de registros entre páginas permanece
    responsabilidade de extrair_registros_pot_pdf().
    """

    registros = []

    for tabela in pagina.find_tables():
        dados = tabela.extract()

        if not dados:
            continue

        layout = _identificar_layout_tabela_pot(dados)

        if layout is None:
            continue

        indice_cabecalho = _localizar_cabecalho_pot(dados)

        if indice_cabecalho is None:
            continue

        for linha in dados[indice_cabecalho + 1:]:
            if not linha:
                continue

            if not any(
                celula and celula.strip()
                for celula in linha
            ):
                continue

            # Ignora linhas auxiliares que não tenham estrutura
            # mínima de seis colunas.
            linha = list(linha)

            while len(linha) < 6:
                linha.append("")

            registro = _registro_pot_da_linha(
                linha,
                layout,
            )

            # Não cria registro para linha sem número e sem
            # qualquer conteúdo nas colunas documentais.
            if not any(
                registro.get(campo)
                for campo in (
                    "numero",
                    "beneficiario",
                    "unidade",
                    "horario_atuacao",
                    "area_aprendizado",
                    "data_inclusao",
                    "data_desligamento",
                    "substituicao",
                )
            ):
                continue

            registros.append(registro)

    return registros

def extrair_registros_pot(texto_bloco):
    """
    Extrai registros POT a partir de texto linearizado.

    Esta função permanece como API pública de compatibilidade.
    A extração estrutural por coordenadas deve ser feita através
    de _extrair_registros_pot_pagina().
    """
    if not texto_bloco:
        return []

    texto = texto_bloco.strip()

    if not PADRAO_CABECALHO_POT.search(texto):
        return []

    # O texto linearizado não possui informação suficiente para
    # reconstruir corretamente a tabela POT.
    #
    # Portanto, a extração definitiva deve ocorrer diretamente
    # sobre a página PDF através de _extrair_registros_pot_pagina().
    return []