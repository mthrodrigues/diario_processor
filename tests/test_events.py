from events import extrair_agente_publico, extrair_eventos_bloco, extrair_participantes_evento, segmentar_sub_eventos, extrair_orgao, limpar_texto_institucional
from main import _timeline_vinculo_valido
from taxonomy.event_taxonomy import (
    DESIGNACAO_FISCAL,
    CONTRATACAO,
    NOMEACAO,
    EXONERACAO
)


def test_designacao_fiscal_reutiliza_contrato_dos_metadados():

    texto = """
    PORTARIA Nº 001/2026

    Designar servidor para acompanhamento e fiscalização do
    Contrato de Locação nº 022.CL.05.2022.
    """

    metadados = {
        "tipo": "portaria",
        "contrato": "022.CL.05.2022",
    }

    eventos = extrair_eventos_bloco(
        metadados,
        texto,
        diario_id=1,
        numero_bloco=1,
    )

    evento = next(
        e for e in eventos
        if e["tipo_evento"] == DESIGNACAO_FISCAL
    )

    assert evento["contrato"] == "022.CL.05.2022"


def test_segmenta_duas_portarias_em_dois_subeventos():

    texto = """
    PORTARIA GP Nº 469/2026

    Designar servidor para acompanhamento e fiscalização do
    Contrato nº 001/2026.

    Processo nº 100/2026.

    PORTARIA GP Nº 470/2026

    Designar servidor para acompanhamento e fiscalização do
    Contrato nº 002/2026.

    Processo nº 200/2026.
    """

    metadados = {
        "tipo": "portaria",
        "contrato": "001/2026",
    }

    eventos = extrair_eventos_bloco(
        metadados,
        texto,
        diario_id=1,
        numero_bloco=1,
    )

    assert len(eventos) == 2


def test_designacoes_fiscais_usam_contrato_do_proprio_subevento():

    texto = """
    PORTARIA GP Nº 102/2026 – NOMEAR, a servidora PRISCILA DE BRITO
    XAVIER FREIRE, matrícula nº 4.20292-1, como responsável pelo
    acompanhamento e fiscalização do Contrato nº 004.012.2025.

    PORTARIA GP Nº 103/2026 – NOMEAR, o servidor
    GUSTAVO BATISTA DE JESUS, matrícula nº 4.20342-4, como responsável
    pelo acompanhamento e fiscalização do Termo de Colaboração nº 001.008.2025.

    PORTARIA GP Nº 104/2026 – NOMEAR, o servidor GUSTAVO BATISTA DE JESUS, matrícula nº 4.20342-4, como responsável pelo acompanhamento e fiscalização do Termo de Colaboração nº 004.05.2022.
    """

    metadados = {
        "tipo": "portaria",
        "contrato": "004.012.2025",
    }

    subeventos = segmentar_sub_eventos(texto)
    eventos = extrair_eventos_bloco(
        metadados,
        texto,
        diario_id=3222,
        numero_bloco=8,
    )

    assert len(subeventos) == 3
    assert [evento["tipo_evento"] for evento in eventos] == [
        DESIGNACAO_FISCAL,
        DESIGNACAO_FISCAL,
        DESIGNACAO_FISCAL,
    ]
    assert [evento["contrato"] for evento in eventos] == [
        "004.012.2025",
        "001.008.2025",
        "004.05.2022",
    ]


def test_contratacao_utiliza_metadados_do_parser():

    texto = """
    EXTRATO DE CONTRATO Nº 015/2026

    Objeto: Prestação de serviços especializados.
    """

    metadados = {
        "tipo": "contrato",
        "contratante_normalizado": "Prefeitura Municipal de Teresópolis",
        "fornecedor_normalizado": "Empresa XPTO LTDA",
        "contrato": "015/2026",
        "processo": "12345/2026",
        "valor_principal": 250000.00,
        "objeto": "Prestação de serviços especializados",
    }

    eventos = extrair_eventos_bloco(
        metadados,
        texto,
        diario_id=1,
        numero_bloco=1,
    )

    assert len(eventos) == 1

    evento = next(
        e for e in eventos
        if e["tipo_evento"] == CONTRATACAO
    )

    assert evento["entidade_origem"]["nome"] == \
        "Prefeitura Municipal de Teresópolis"

    assert evento["entidade_destino"]["nome"] == \
        "Empresa XPTO LTDA"

    assert evento["contrato"] == "015/2026"
    assert evento["processo"] == "12345/2026"
    assert evento["valor"] == 250000.00
    assert evento["objeto"] == "Prestação de serviços especializados"

def test_contratacao_nao_gera_evento_sem_fornecedor():

    texto = """
    EXTRATO DE CONTRATO Nº 015/2026
    """

    metadados = {
        "tipo": "contrato",
        "contratante_normalizado": "Prefeitura Municipal de Teresópolis",
        "fornecedor_normalizado": None,
        "contrato": "015/2026",
        "processo": "12345/2026",
        "valor_principal": 250000.00,
        "objeto": "Prestação de serviços especializados",
    }

    eventos = extrair_eventos_bloco(
        metadados,
        texto,
        diario_id=1,
        numero_bloco=1,
    )

    assert eventos == []

def test_contratacao_nao_gera_evento_sem_contratante():

    texto = """
    EXTRATO DE CONTRATO Nº 015/2026
    """

    metadados = {
        "tipo": "contrato",
        "contratante_normalizado": None,
        "fornecedor_normalizado": "Empresa XPTO LTDA",
        "contrato": "015/2026",
        "processo": "12345/2026",
        "valor_principal": 250000.00,
        "objeto": "Prestação de serviços especializados",
    }

    eventos = extrair_eventos_bloco(
        metadados,
        texto,
        diario_id=1,
        numero_bloco=1,
    )

    assert eventos == []

def test_nomeacao_gera_evento_com_agente_cargo_e_orgao():

    texto = """
    PORTARIA Nº 100/2026

    NOMEAR JOÃO DA SILVA para exercer o Cargo em Comissão de
    Diretor de Compras, Símbolo CC-2, lotado na Secretaria
    Municipal de Administração.
    """

    metadados = {
        "tipo": "portaria",
    }

    eventos = extrair_eventos_bloco(
        metadados,
        texto,
        diario_id=1,
        numero_bloco=1,
    )

    assert len(eventos) == 1

    evento = next(
        e for e in eventos
        if e["tipo_evento"] == NOMEACAO
    )

    assert evento["agente"]["nome"] == "JOÃO DA SILVA"
    assert evento["cargo"] == "Diretor de Compras"
    assert evento["orgao"] == "Secretaria Municipal de Administração"

def test_exoneracao_gera_evento_com_agente_cargo_e_orgao():

    texto = """
    PORTARIA Nº 101/2026

    EXONERAR JOÃO DA SILVA do Cargo em Comissão de
    Diretor de Compras, Símbolo CC-2, lotado na
    Secretaria Municipal de Administração.
    """

    metadados = {
        "tipo": "portaria",
    }

    eventos = extrair_eventos_bloco(
        metadados,
        texto,
        diario_id=1,
        numero_bloco=1,
    )

    assert len(eventos) == 1

    evento = next(
        e for e in eventos
        if e["tipo_evento"] == EXONERACAO
    )

    assert evento["agente"]["nome"] == "JOÃO DA SILVA"
    assert evento["cargo"] == "Diretor de Compras"
    assert evento["orgao"] == "Secretaria Municipal de Administração"


def test_timeline_vinculo_requer_pessoa_e_orgao():
    assert _timeline_vinculo_valido(NOMEACAO, None, None) is False
    assert _timeline_vinculo_valido(NOMEACAO, 10, None) is False
    assert _timeline_vinculo_valido(NOMEACAO, None, 20) is False
    assert _timeline_vinculo_valido(NOMEACAO, 10, 20) is True
    assert _timeline_vinculo_valido(EXONERACAO, 10, 20) is True
    assert _timeline_vinculo_valido(DESIGNACAO_FISCAL, 10, 20) is False


def _obter_participantes(evento):
    """
    Retorna a colecao de participantes associados ao evento.
    Suporta o modelo de multiplos participantes ('participantes' ou 'agentes')
    e retrocompatibilidade com o formato legado de agente singular ('agente').
    """
    if "participantes" in evento and evento["participantes"] is not None:
        return list(evento["participantes"])
    if "agentes" in evento and evento["agentes"] is not None:
        return list(evento["agentes"])
    agente = evento.get("agente")
    if isinstance(agente, dict) and agente.get("nome"):
        return [agente]
    return []


def _extrair_nomes_participantes(evento):
    """
    Retorna lista normalizada em caixa alta com os nomes dos participantes do evento.
    """
    participantes = _obter_participantes(evento)
    nomes = []
    for p in participantes:
        if isinstance(p, dict):
            nome = p.get("nome")
            if nome:
                nomes.append(nome.strip().upper())
        elif isinstance(p, str):
            nomes.append(p.strip().upper())
    return nomes


def test_multiplos_participantes_caso_a_portaria_gp_89():
    """
    Caso A: Diario 3217 / bloco 12 / Portaria GP 89 (CACS/FUNDEB).
    Protege:
    - Exatamente 1 evento NOMEACAO (unidade do ato administrativo, nao criar 1 por pessoa);
    - Multiplos participantes associados ao mesmo ato.
    """
    texto = """PORTARIA GP Nº 89, DE 07 DE JANEIRO DE 2026.
DISPÕE SOBRE SUBSTITUIÇÃO.
O PREFEITO MUNICIPAL DE TERESÓPOLIS, usando das atribuições que lhe confere a
legislação em vigor,
RESOLVE:
Art. 1º NOMEAR, em substituição, para compor o Conselho Municipal de Acompanhamento e
Controle Social do Fundo de Manutenção e Desenvolvimento da Educação Básica e de
Valorização dos Profissionais da Educação – CACS/FUNDEB, nomeado mediante Portaria GP nº
375/2023 e alterado pelas Portarias GP nºs 516/2023, 584/2023, 593/2023, 317/2024, 837/2024,
1.467/2024, 883/2025, 1.220/2025 e 1.485/2025 os representantes abaixo relacionados, em
conformidade com a Lei Municipal nº 3.990/2021, conforme Processo Administrativo nº
2.357/2023:
I - Representantes do Poder Executivo Municipal:
De:
Titular: José Nildo Onofre de Amorim
Suplente: Victor Rossetti Netto dos Reys Burns
Para:
Titular: Victor Rossetti Netto dos Reys Burns
Suplente: Janderson Alex de Oliveira Gonçalves
II - Representantes dos Pais de Alunos da Educação Básica Pública:
De:
Titular: Cargo Vago
Suplente: Cargo Vago
Titular: Elaine Cristina Maia Ribeiro
Suplente: Cargo Vago
Para:
Titular: Carla Regina Ribeiro da Silva Gonçalves
Suplente: Ana Cláudia Mendes Oliveira
Titular: Gisele Pacheco Dias
Suplente: Natália Natal de Oliveira
Art. 2º A presente Portaria entra em vigor na data de sua publicação, produzindo efeitos a partir
de 03/12/2025.
JOSÉ LEONARDO VASCONCELLOS DE ANDRADE
= Prefeito ="""

    metadados = {
        "tipo": "portaria",
        "processo": "2.357/2023",
    }

    eventos = extrair_eventos_bloco(
        metadados,
        texto,
        diario_id=3217,
        numero_bloco=12,
    )

    assert len(eventos) == 1, (
        f"Deve gerar exatamente 1 evento NOMEACAO para o ato, mas gerou {len(eventos)}"
    )
    evento = eventos[0]
    assert evento["tipo_evento"] == NOMEACAO

    participantes = _obter_participantes(evento)
    assert len(participantes) > 1, (
        f"Ato colegiado com multiplos participantes nao deve ter 0 ou 1 participante: {participantes}"
    )

    nomes = _extrair_nomes_participantes(evento)
    assert any("VICTOR ROSSETTI NETTO DOS REYS BURNS" in n for n in nomes), (
        f"Victor Rossetti Netto dos Reys Burns deve constar nos participantes: {nomes}"
    )
    assert any("JANDERSON ALEX DE OLIVEIRA" in n for n in nomes), (
        f"Janderson Alex de Oliveira Goncalves deve constar nos participantes: {nomes}"
    )


def test_multiplos_participantes_caso_b_portaria_gp_406():
    """
    Caso B: Diario 3297 / bloco 16 / Portaria GP 406 (CACS/FUNDEB).
    Protege:
    - Exatamente 1 evento NOMEACAO (nao criar dois eventos);
    - Thaiane e Giovanni devem ser representados como participantes distintos.
    """
    texto = """PORTARIA GP Nº 406, DE 30 DE MARÇO DE 2026.
DISPÕE SOBRE SUBSTITUIÇÃO.
O PREFEITO MUNICIPAL DE TERESÓPOLIS, usando das atribuições que lhe
confere a legislação em vigor,
RESOLVE:
Art. 1º NOMEAR, em substituição, para compor o Conselho Municipal de
Acompanhamento e Controle Social do Fundo de Manutenção e Desenvolvimento da
Educação Básica e de Valorização dos Profissionais da Educação – CACS/FUNDEB,
nomeado mediante Portaria GP nº 375/2023 e alterado pelas Portarias GP nºs 516/2023,
584/2023, 593/2023, 317/2024, 837/2024, 1.467/2024, 883/2025, 1.220/2025, 1.485/2025
e 89/2026 os representantes abaixo relacionados, em conformidade com a Lei Municipal
nº 3.990/2021, conforme Processo Administrativo nº 2.357/2023:
I - Representantes do Conselho Tutelar:
De:
Titular: Thaiane Gomes da Costa
Para:
Titular: Giovanni Moreira da Matos
Art. 2º A presente Portaria entra em vigor na data de sua publicação, produzindo efeitos
a partir de 19/03/2026.
JOSÉ LEONARDO VASCONCELLOS DE ANDRADE
= Prefeito ="""

    metadados = {
        "tipo": "portaria",
        "processo": "2.357/2023",
    }

    eventos = extrair_eventos_bloco(
        metadados,
        texto,
        diario_id=3297,
        numero_bloco=16,
    )

    assert len(eventos) == 1, (
        f"Deve gerar exatamente 1 evento NOMEACAO para o ato, mas gerou {len(eventos)}"
    )
    evento = eventos[0]
    assert evento["tipo_evento"] == NOMEACAO

    participantes = _obter_participantes(evento)
    nomes = _extrair_nomes_participantes(evento)

    assert any("THAIANE GOMES DA COSTA" in n for n in nomes), (
        f"Thaiane Gomes da Costa deve constar nos participantes: {nomes}"
    )
    assert any("GIOVANNI MOREIRA DA MATOS" in n for n in nomes), (
        f"Giovanni Moreira da Matos deve constar nos participantes: {nomes}"
    )
    assert len(set(nomes)) >= 2, (
        f"Thaiane e Giovanni devem ser representados como participantes distintos: {nomes}"
    )

def test_multiplos_participantes_caso_c_portaria_gp_351_2026():
    """
    Caso C: Diario 3281 / bloco 2 / Portaria GP 351/2026 (DESIGNACAO_FISCAL).
    Protege:
    - Exatamente 1 evento DESIGNACAO_FISCAL (nao criar um evento por pessoa);
    - Flavia e Karoline devem ser representadas como participantes distintas.
    """
    texto = """PORTARIA GP Nº 351/2026 – NOMEAR, as servidoras FLAVIA MEDEIROS TAYT-SOHN, matrícula nº 4.0345-7, e KAROLINE BITTENCOURT MEDAS, matrícula nº 2.30280-0, em substituição ao Sr. RENATO LOPES XAVIER, como responsáveis pelo acompanhamento e fiscalização do Contrato de Locação nº 022.CL.05.2022 e todos os seus aditivos, firmado entre a Prefeitura Municipal de Teresópolis através do Fundo Municipal de Saúde e Mitra Diocesana de Petrópolis, cujo objeto é a locação do imóvel situado na Rua Monsenhor Nivaldo, n° 342 - Alto, Teresópolis/RJ, para funcionamento de um Posto de Saúde da Família - PSF, com efeitos a partir de 08/01/2026, conforme Memorando nº 4.453/2026."""

    metadados = {
        "tipo": "portaria",
        "contrato": "022.CL.05.2022",
    }

    eventos = extrair_eventos_bloco(
        metadados,
        texto,
        diario_id=3281,
        numero_bloco=2,
    )

    assert len(eventos) == 1, (
        f"Deve gerar exatamente 1 evento DESIGNACAO_FISCAL para o ato, mas gerou {len(eventos)}"
    )
    evento = eventos[0]
    assert evento["tipo_evento"] == DESIGNACAO_FISCAL

    participantes = _obter_participantes(evento)
    nomes = _extrair_nomes_participantes(evento)

    assert any("FLAVIA MEDEIROS TAYT-SOHN" in n for n in nomes), (
        f"Flavia Medeiros Tayt-Sohn deve constar nos participantes: {nomes}"
    )
    assert any("KAROLINE BITTENCOURT MEDAS" in n for n in nomes), (
        f"Karoline Bittencourt Medas deve constar nos participantes: {nomes}"
    )
    assert len(set(nomes)) >= 2, (
        f"Flavia e Karoline devem ser representadas como participantes distintas: {nomes}"
    )

def test_multiplos_participantes_funcionarios_comissao_meio_ambiente():
    texto = """PORTARIA SMMA Nº 1/2026, de 26 de Fevereiro de 2026.
O Secretário Municipal de Meio Ambiente, usando das atribuições que lhe confere a
legislação em vigor:
RESOLVE:
NOMEAR, nos termos do Art. 1º, inciso IV, da Lei Municipal 1.477/93, os funcionários
André Luiz Ramos, matrícula nº 1.14478-2, Emerson da Silva Lima, matrícula nº 1.11455-7,
Marcelo Martins Rodrigues, matrícula nº 1.08566-3, Sidnei de Oliveira Pacheco,
matrícula 1.11276-7, Vitor Francisco da Rosa, matrícula 1.12332-7, Paulo Sergio
Bandeira, matrícula nº 1.12732-2, Raphael Pinto de Carvalho Rebello, matrícula 1.12376-9
e Rita de Cássia Pereira de Oliveira, matrícula 1.12543-5, para integrarem a comissão
de Fiscalização de Meio Ambiente pelo prazo de 120 (cento e vinte) dias com efeitos a
partir de 02 de março de 2026."""

    participantes = extrair_participantes_evento(texto)

    nomes = [p["nome"] for p in participantes]

    assert len(nomes) == 8
    assert "ANDRÉ LUIZ RAMOS" in [n.upper() for n in nomes]
    assert "EMERSON DA SILVA LIMA" in [n.upper() for n in nomes]
    assert "MARCELO MARTINS RODRIGUES" in [n.upper() for n in nomes]
    assert "SIDNEI DE OLIVEIRA PACHECO" in [n.upper() for n in nomes]
    assert "VITOR FRANCISCO DA ROSA" in [n.upper() for n in nomes]
    assert "PAULO SERGIO BANDEIRA" in [n.upper() for n in nomes]
    assert "RAPHAEL PINTO DE CARVALHO REBELLO" in [n.upper() for n in nomes]
    assert "RITA DE CÁSSIA PEREIRA DE OLIVEIRA" in [n.upper() for n in nomes]


def test_ato_singular_produz_unico_participante_compatibilidade():
    """
    Compatibilidade: ato singular simples com um unico servidor.
    Protege:
    - Um ato com um unico agente continua produzindo exatamente 1 participante;
    - Comportamento de atos simples nao regride.
    """
    texto = """
    PORTARIA Nº 100/2026

    NOMEAR JOÃO DA SILVA para exercer o Cargo em Comissão de
    Diretor de Compras, Símbolo CC-2, lotado na Secretaria
    Municipal de Administração.
    """

    metadados = {
        "tipo": "portaria",
    }

    eventos = extrair_eventos_bloco(
        metadados,
        texto,
        diario_id=1,
        numero_bloco=1,
    )

    assert len(eventos) == 1
    evento = eventos[0]
    assert evento["tipo_evento"] == NOMEACAO

    participantes = _obter_participantes(evento)
    assert len(participantes) == 1, (
        f"Ato singular deve ter exatamente 1 participante, obteve {len(participantes)}"
    )

    nomes = _extrair_nomes_participantes(evento)
    assert nomes == ["JOÃO DA SILVA"]
    assert evento.get("agente", {}).get("nome") == "JOÃO DA SILVA"

def test_extrair_orgao_municipio_atraves_da_secretaria():
    texto = (
        "firmado entre o Município de Teresópolis através da "
        "Secretaria Municipal de Saúde e o Instituto Atitude de Desenvolvimento - IAD"
    )

    assert extrair_orgao(texto) == "Secretaria Municipal de Saúde"

def test_limpar_texto_institucional_preserva_secretaria_apos_municipio():
    texto = (
        "firmado entre o Município de Teresópolis através da "
        "Secretaria Municipal de Saúde e o Instituto Atitude de Desenvolvimento - IAD"
    )

    texto_limpo = limpar_texto_institucional(texto)

    assert "Secretaria Municipal de Saúde" in texto_limpo

def test_extrair_orgao_fundo_municipal_apos_o():
    casos = [
        (
            "firmado entre o Fundo Municipal de Assistência Social e Darci Ramos Tavares",
            "Fundo Municipal de Assistência Social",
        ),
        (
            "firmado entre o Fundo Municipal de Saúde de Teresópolis e a Empresa Medi Saúde Laboratório e Imagem Ltda.",
            "Fundo Municipal de Saúde de Teresópolis",
        ),
        (
            "firmado entre o Fundo Municipal dos Direitos da Criança e do Adolescente de Teresópolis e o Centro Integrado de Estudos e Programas de Desenvolvimento Social - CIEDS",
            "Fundo Municipal dos Direitos da Criança e do Adolescente de Teresópolis",
        ),
    ]

    for texto, esperado in casos:
        assert extrair_orgao(texto) == esperado

def test_extrair_orgao_prefeitura_municipal():
    texto = (
        "firmado entre a Prefeitura Municipal de Teresópolis "
        "e a Cooperativa de Crédito Credirochas"
    )

    assert extrair_orgao(texto) == "Prefeitura Municipal de Teresópolis"

def test_extrair_orgao_procuradoria_geral():
    texto = (
        "firmado entre o Município de Teresópolis através da "
        "Procuradoria Geral do Município e a Empresa Metaway Tecnologia"
    )

    assert extrair_orgao(texto) == "Procuradoria Geral do Município"

def test_extrair_orgao_procuradoria_geral_em_nomeacao():
    texto = (
        "NOMEAR JOÃO DA SILVA para exercer o Cargo em Comissão de "
        "Assessor Especial, na Procuradoria Geral, a partir de 01/04/2026."
    )

    assert extrair_orgao(texto) == "Procuradoria Geral"


def test_extrair_orgao_procuradoria_geral_em_exoneracao():
    texto = (
        "EXONERAR JOÃO DA SILVA do Cargo em Comissão de "
        "Assessor Especial, da Procuradoria Geral, com efeitos a partir de 01/04/2026."
    )

    assert extrair_orgao(texto) == "Procuradoria Geral"

def test_extrair_orgao_secretaria_obras():
    texto = (
        "firmado entre a Secretaria de Obras e Serviços Públicos "
        "e a Empresa Industria e Comércio de Pedras Vale Alpino Ltda."
    )

    assert extrair_orgao(texto) == "Secretaria de Obras e Serviços Públicos"

def test_extrair_orgao_municipio_contratante():
    texto = (
        "firmado entre o Município de Teresópolis "
        "e a Empresa MPJ Distribuidora de Produtos Hospitalares Ltda."
    )

    assert extrair_orgao(texto) == "Município de Teresópolis"

def test_extrair_orgao_nao_invade_publicacao_seguinte():
    texto = (
        "PORTARIA GP Nº 338/2026 – NOMEAR, o servidor RAFAEL TRESSI GERALDO, "
        "como responsável pelo acompanhamento e fiscalização do Contrato nº 002.012.2026, "
        "firmado entre o Fundo Municipal de Saúde de Teresópolis e a Empresa Global Med "
        "Serviços Ltda., tendo por objeto ... "
        "Prefeitura Municipal de Teresópolis, em 06 de março de 2026. "
        "JOSÉ LEONARDO ... = Prefeito = "
        "SECRETARIA MUNICIPAL DE MEIO AMBIENTE - CONSELHO MUNICIPAL..."
    )

    assert extrair_orgao(texto[:2000]) == "Fundo Municipal de Saúde de Teresópolis"

def test_extrair_agente_publico_sem_virgula_antes_da_matricula():
    texto = (
        "NOMEAR, o servidor ARIEL HAYASAKI DOS SANTOS matrícula "
        "4.20304-6, como responsável pelo acompanhamento e fiscalização "
        "do Contrato nº 039.012.2025."
    )

    assert extrair_agente_publico(texto) == "ARIEL HAYASAKI DOS SANTOS"

def test_multiplos_participantes_remove_matriculas_com_quebra_de_linha():
    texto = """NOMEAR, nos termos do Art. 1º, inciso IV, da Lei Municipal 1.477/93, os funcionários
André Luiz Ramos, matrícula nº 1.14478-2, Emerson da Silva Lima, matrícula nº 1.11455-
7, Marcelo Martins Rodrigues, matrícula nº 1.08566-3, Sidnei de Oliveira Pacheco,
matrícula 1.11276-7, Vitor Francisco da Rosa, matrícula 1.12332-7, Paulo Sergio
Bandeira, matrícula nº 1.12732-2, Raphael Pinto de Carvalho Rebello, matrícula 1.12376-
9 e Rita de Cássia Pereira de Oliveira, matrícula 1.12543-5, para integrarem a comissão
de Fiscalização de Meio Ambiente."""

    participantes = extrair_participantes_evento(texto)

    nomes = [p["nome"] for p in participantes]

    assert len(nomes) == 8
    assert "EMERSON DA SILVA LIMA" in [n.upper() for n in nomes]
    assert "RAPHAEL PINTO DE CARVALHO REBELLO" in [n.upper() for n in nomes]

    assert all(not n.endswith((" 7", " 9")) for n in nomes)

def test_extrair_agente_publico_aceita_virgula_apos_nomear():
    texto = """
    PORTARIA GP Nº 329/2026 – NOMEAR, nos termos do art. 9º da Lei
    Complementar Municipal nº 167/2013 (ESTATUTO), c/c a Lei Municipal nº
    1.441/1993 e alterações posteriores, MARIA EDUARDA LEOPOLDO DUARTE,
    para exercer o Cargo em Comissão de Chefe da Divisão de Marcação de
    Exames, Símbolo DAS-3, Cód. 40628, na Secretaria Municipal de Saúde.
    """

    assert (
        extrair_agente_publico(texto)
        == "MARIA EDUARDA LEOPOLDO DUARTE"
    )


def test_extrair_agente_publico_aceita_virgula_antes_de_para():
    texto = """
    PORTARIA GP Nº 329/2026 – NOMEAR nos termos do art. 9º da Lei
    Complementar Municipal nº 167/2013 (ESTATUTO), c/c a Lei Municipal nº
    1.441/1993 e alterações posteriores, MARIA EDUARDA LEOPOLDO DUARTE,
    para exercer o Cargo em Comissão de Chefe da Divisão de Marcação de
    Exames, Símbolo DAS-3, Cód. 40628, na Secretaria Municipal de Saúde.
    """

    assert (
        extrair_agente_publico(texto)
        == "MARIA EDUARDA LEOPOLDO DUARTE"
    )


def test_extrair_agente_publico_nao_descarta_nome_contendo_lei():
    texto = """
    PORTARIA GP Nº 480/2026 – NOMEAR nos termos do art. 9º da Lei
    Complementar Municipal nº 167/2013 (ESTATUTO), c/c a Lei Municipal nº
    1.441/1993 e alterações posteriores, CLEITON EVANDRO CORREA PIMENTEL,
    matrícula nº 4.20303-0, para exercer o Cargo em Comissão de Agente de
    Defesa Civil, Símbolo DAS-1, Cód. 40276.
    """

    assert (
        extrair_agente_publico(texto)
        == "CLEITON EVANDRO CORREA PIMENTEL"
    )


def test_extrair_agente_publico_aceita_apostrofo_no_nome():
    texto = """
    PORTARIA GP Nº 768/2026 – NOMEAR nos termos do art. 9º da Lei
    Complementar Municipal nº 167/2013 (ESTATUTO), c/c a Lei Municipal nº
    1.441/1993 e alterações posteriores, CLÁUDIO JOSÉ SANT'ANA, para
    exercer o Cargo em Comissão de Assessor Administrativo, Símbolo DAS-3,
    Cód. 40711, na Procuradoria Geral.
    """

    assert (
        extrair_agente_publico(texto)
        == "CLÁUDIO JOSÉ SANT'ANA"
    )