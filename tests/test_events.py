from events import (
    extrair_agente_publico,
    extrair_cargo,
    extrair_eventos_bloco,
    extrair_participantes_evento,
    extrair_servidores_designados,
    segmentar_sub_eventos,
    extrair_orgao,
    limpar_texto_institucional,
    extrair_numero_portaria_gp,
)

from main import _timeline_vinculo_valido
from taxonomy.entity_taxonomy import PESSOA
from taxonomy.event_taxonomy import (
    DESIGNACAO,
    DESIGNACAO_FISCAL,
    CONTRATACAO,
    DISPENSA,
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


def test_extrair_orgao_corregedoria_guarda_civil_municipal_diario_3246_bloco_17():
    texto = """
    PORTARIA SMSOPM Nº 2/2026, de 04 de Fevereiro de 2026.
    Ver consolidado Comissão Permanente de Sindicância e
    Processo Administrativo Disciplinar da
    Guarda Civil Municipal
    O Corregedor da Guarda Civil Municipal, no uso de suas atribuições legais, e tendo em
    vista o disposto lhe confere o Art. 48 da Lei 4.340 de 27 de abril de 2023 da Lei Municipal
    e no art. 149 da Lei Federal nº 8.112
    RESOLVE:
    Institui a Comissão Permanente de Sindicância e Processo Administrativo Disciplinar no
    âmbito do Corregedoria da Guarda Civil Municipal vinculada à Secretaria de Segurança,
    Ordem Pública e Mobilidade para o ano de 2026.
    Art. 1º Instituir a Comissão Permanente de Sindicância e Processo Administrativo
    Disciplinar da Corregedoria com o objetivo de apurar supostas infrações disciplinares,
    conduzir sindicâncias investigativas, processuais e procedimentos administrativos
    disciplinares, bem como promover orientação administrativa.
    Art. 2º Designar os servidores estáveis abaixo relacionados para compor a r
    """

    assert extrair_orgao(texto) == "Corregedoria da Guarda Civil Municipal"


def test_extrair_orgao_nao_infere_corregedoria_de_cargo_diario_3249_bloco_6():
    texto = """
    PORTARIA SMSOPM Nº 3/2026, de 05 de Fevereiro de 2026.
    Ver consolidado
    Dispõe sobre a instauração de Sindicância
    contraditória.
    O Corregedor da Guarda Civil Municipal de
    Teresópolis, no uso das atribuições previstas no Art. 48 da Lei 4.340 de 27 de abril de
    2023 e tendo em vista o disposto nos artigos
    143, 148 e 149 da Lei nº 8.112, de 11 de
    dezembro de 1990,
    RESOLVE:
    Art. 1º Instaurar Sindicância Contraditória, visando à apuração de eventuais
    responsabilidades administrativas descritas no protocolo da ouvidoria geral nº: 2860653,
    bem como proceder ao exame dos atos e fatos conexos que emergirem no curso dos
    trabalhos.
    Art. 2º Designar para compor a Comissão de Processo Administrativo Disciplinar os
    servidores: Gean Fabrizio Teixeira de Almada. Mat. 1.07537-4, Gustavo Passos dos
    Santos. Mat. 1.09169-8. e Marcela Félix da Silva. Mat. 1.12393-9, para, sob a presidência
    do primeiro, realizar os trabalhos apurados e apresentar relatório conclusivo no prazo
    previsto em Lei.
    Art. 3º A Comiss
    """

    assert extrair_orgao(texto) is None


def test_extrair_orgao_nao_infere_corregedoria_de_cargo_diario_3333_bloco_10():
    texto = """
    PORTARIA COR.GCM Nº 4, de 12 de Maio de 2026.
    Dispõe sobre a instauração de Sindicância
    Acusatória.
    O Corregedor da Guarda Civil Municipal de Teresópolis, no uso das atribuições previstas
    no Art. 48 da Lei 4.340 de 27 de abril de 2023 e tendo em vista o disposto nos artigos
    143, 148 e 149 da Lei nº 8.112, de 11 de dezembro de 1990,
    RESOLVE:
    Art. 1º Instaurar Sindicância acusatória, visando à apuração de eventuais
    responsabilidades administrativas descritas no Memorando Interno da Guarda Civil
    Municipal nº: 22.009/2025, bem como proceder ao exame dos atos e fatos conexos que
    emergirem no curso dos trabalhos.
    Art. 2º Designar para compor a Comissão de Processo Administrativo Disciplinar os
    servidores: Gean Fabrizio Teixeira de Almada. Mat. 1.07537-4, Gustavo Passos dos
    Santos. Mat. 1.09169-8. e Vagner Machado Roberto. Mat. 1.1, para, sob a presidência do
    primeiro, realizar os trabalhos apurados e apresentar relatório conclusivo no prazo
    previsto em Lei.
    Art. 3º A Comissão deverá proceder
    """

    assert extrair_orgao(texto) is None


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

def test_extrair_servidores_designados_remove_prefixo_humano_dos_participantes():
    texto = """
    PORTARIA GP Nº 136/2026 – NOMEAR, a servidora FABIANA CANTO GRANGEIRO,
    matrícula nº 4.20349-4 e o servidor OSINEI DE OLIVEIRA, matrícula nº 1.11521-9,
    como responsáveis pelo acompanhamento e fiscalização do Contrato nº 012.008.2025
    e seus respectivos aditivos e apostilamentos.
    """

    participantes = extrair_servidores_designados(texto)

    assert participantes == [
        {
            "tipo": PESSOA,
            "nome": "FABIANA CANTO GRANGEIRO",
        },
        {
            "tipo": PESSOA,
            "nome": "OSINEI DE OLIVEIRA",
        },
    ]

def test_extrair_agente_publico_exoneracao_aceita_virgula_antes_de_do_cargo():
    texto = """
    PORTARIA GP Nº 483/2026 – EXONERAR, nos termos do art. 38 da Lei
    Complementar Municipal nº 167/2013 (ESTATUTO), FABIANO THOMAZ CARRIONE, do
    Cargo em Comissão de Secretário de Conselho de Recursos Fiscais, Símbolo DAS-1,
    Cód. 40110, da Secretaria Municipal de Finanças e Orçamento, a partir de 01/05/2026
    (Memorando SMGC nº 05/2026).
    """

    assert (
        extrair_agente_publico(texto)
        == "FABIANO THOMAZ CARRIONE"
    )

def test_exoneracao_extrai_cargo_com_quebra_de_linha_e_interino():
    casos = [
        (
            """
            PORTARIA GP Nº 434/2026 –
            EXONERAR, nos termos do art. 38 da Lei Complementar Municipal nº 167/2013
            (ESTATUTO), JOSÉ CARLOS FITA NOGUEIRA, matrícula nº 4.70001-8, do Cargo em
            Comissão de Secretário Municipal de Limpeza Pública, Símbolo DAS-6, a partir de
            09/04/2026 (Memorando nº 7.556/2026).
            """,
            "Secretário Municipal de Limpeza Pública",
        ),
        (
            """
            PORTARIA GP Nº 119/2026 –
            EXONERAR, nos termos do art. 38 da Lei Complementar Municipal nº 167/2013
            (ESTATUTO), DAVI RIBEIRO SERAFIM, matrícula nº 1.07728-0, do Cargo em
            Comissão, interino, de Secretário Municipal de Obras e Serviços Públicos,
            Símbolo DAS-6, Cód. 40737, com efeitos a partir de 05/01/2026
            (Memorando nº 362/2026).
            """,
            "Secretário Municipal de Obras e Serviços Públicos",
        ),
    ]

    for texto, cargo_esperado in casos:
        eventos = extrair_eventos_bloco(
            {"tipo": "portaria"},
            texto,
            diario_id=1,
            numero_bloco=1,
        )

        evento = next(
            e for e in eventos
            if e["tipo_evento"] == EXONERACAO
        )

        assert evento["cargo"] == cargo_esperado

def test_exoneracao_extrai_cargo_sem_preposicao_de():
    casos = [
        (
            """
            PORTARIA GP Nº 272/2026 –
            EXONERAR, a pedido, nos termos do art. 37 da Lei Complementar Municipal nº
            167/2013 (ESTATUTO), KATIA REGINA DE AQUINO PAZ, matrícula nº 1.11919-2, do
            Cargo Professor I, lotado na Secretaria Municipal de Educação, com efeitos a partir de
            01/02/2026 (Protocolo nº 3.681/2026).
            """,
            "Professor I",
        ),
        (
            """
            EXONERAR, a pedido, nos termos do art. 37 da Lei Complementar Municipal nº
            167/2013 (ESTATUTO), CARLOS JOSE BAUER DA SILVA, matrícula nº 1.19497-2,
            do Cargo Professor I, lotado na Secretaria Municipal de Educação, com efeitos a
            partir de 02/02/2026.
            """,
            "Professor I",
        ),
        (
            """
            EXONERAR, a pedido, nos termos do art. 37 da Lei Complementar Municipal nº
            167/2013 (ESTATUTO), DEBORA DA PAZ GOMES BRANDÃO FERRAZ, matrícula nº
            1.20175-9, do Cargo Professor I, lotado na Secretaria Municipal de Educação,
            com efeitos a partir de 23/02/2026.
            """,
            "Professor I",
        ),
        (
            """
            EXONERAR, a pedido, nos termos do art. 37 da Lei Complementar Municipal nº
            167/2013 (ESTATUTO), ELIANE BASTOS SALOMÃO, matrícula nº 1.19331-6, do
            Cargo Professor I, lotada na Secretaria Municipal de Educação, com efeitos a
            partir de 01/06/2026.
            """,
            "Professor I",
        ),
        (
            """
            EXONERAR, a pedido, nos termos do art. 37 da Lei Complementar Municipal nº
            167/2013 (ESTATUTO), CAROLINA ALVES GOMES DE OLIVEIRA, matrícula nº
            1.20172-1, do Cargo Professor I, lotada na Secretaria Municipal de Educação,
            com efeitos a partir de 03/08/2026.
            """,
            "Professor I",
        ),
        (
            """
            EXONERAR, a pedido, nos termos do art. 37 da Lei Complementar Municipal nº
            167/2013 (ESTATUTO), BRUNA CORREA DA SILVA, matrícula nº 1.13233-4, do
            Cargo GOS III Auxiliar de Saúde Bucal, lotada na Secretaria Municipal de Saúde,
            com efeitos a partir de 03/08/2026.
            """,
            "GOS III Auxiliar de Saúde Bucal",
        ),
        (
            """
            EXONERAR, a pedido, nos termos do art. 37 da Lei Complementar Municipal nº
            167/2013 (ESTATUTO), FLAVIA MACÊDO DA SILVA, matrícula nº 1.20173-8, do
            Cargo Professor I, lotada na Secretaria Municipal de Educação, com efeitos a
            partir de 26/08/2026.
            """,
            "Professor I",
        ),
        (
            """
            PORTARIA GP Nº 775, DE 10 DE SETEMBRO DE 2026.
            DISPÕE SOBRE EXONERAÇÃO DE CARGO EFETIVO.
            O PREFEITO MUNICIPAL DE TERESÓPOLIS, usando das atribuições que lhe confere
            a legislação em vigor, RESOLVE:
            EXONERAR, a pedido, nos termos do art. 37 da Lei Complementar Municipal nº
            167/2013 (ESTATUTO), THIAGO SANTOS DE ARAUJO, matrícula nº 1.19349-4, do
            Cargo Professor I, lotado na Secretaria Municipal de Educação, com efeitos a
            partir de 25/08/2026.
            """,
            "Professor I",
        ),
    ]

    for texto, cargo_esperado in casos:
        eventos = extrair_eventos_bloco(
            {"tipo": "portaria"},
            texto,
            diario_id=1,
            numero_bloco=1,
        )
        evento = next(
            e for e in eventos if e["tipo_evento"] == EXONERACAO
        )
        assert evento["cargo"] == cargo_esperado

def test_extrair_numero_portaria_gp():
    """
    Protege a extração do identificador da Portaria GP a partir do texto
    do ato administrativo.

    Caso real:
    Diário 3216 / Portaria GP nº 23/2026.

    Regra esperada:
    "PORTARIA GP Nº 23/2026"
    -> "23/2026"
    """
    texto = """
    PORTARIA GP Nº 23/2026 – DISPENSAR, CHRISTIANNE RAQUEL TAVARES DE LIMA,
    matrícula nº 1.14140-6, da Gratificação de Gestão Escolar - GGE,
    de Orientador Pedagógico (Escola "E"), Símbolo GGE-3,
    da Secretaria Municipal de Educação, com efeitos a partir de 02/01/2026.
    """

    assert extrair_numero_portaria_gp(texto) == "23/2026"

def test_extrair_numero_portaria_gp_aceita_numero_com_simbolo_graus():
    texto = """
    PORTARIA GP N° 24/2026 – DESIGNAR, JOÃO DA SILVA,
    para exercer determinada função.
    """

    assert extrair_numero_portaria_gp(texto) == "24/2026"

def test_nomeacao_preserva_numero_portaria_gp():
    """
    Protege a associação do identificador da Portaria GP ao evento
    correspondente.
    """
    texto = """
    PORTARIA GP Nº 100/2026 – NOMEAR JOÃO DA SILVA para exercer o
    Cargo em Comissão de Diretor de Compras, Símbolo CC-2,
    lotado na Secretaria Municipal de Administração.
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
    assert evento["numero_portaria_gp"] == "100/2026"

def test_eventos_preservam_numero_da_propria_portaria_gp():
    """
    Protege a associação entre cada Portaria GP e o evento correspondente.

    Uma mesma publicação pode conter várias Portarias GP.
    Cada evento deve carregar o identificador da sua própria Portaria.
    """
    texto = """
    PORTARIA GP Nº 469/2026
    NOMEAR JOÃO DA SILVA para exercer o Cargo em Comissão de
    Diretor de Compras, Símbolo CC-2, lotado na Secretaria
    Municipal de Administração.

    PORTARIA GP Nº 470/2026
    NOMEAR MARIA DA SILVA para exercer o Cargo em Comissão de
    Diretora de Recursos Humanos, Símbolo CC-3, lotada na Secretaria
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

    assert len(eventos) == 2

    assert [
        evento["numero_portaria_gp"]
        for evento in eventos
    ] == [
        "469/2026",
        "470/2026",
    ]

def test_dispensa_gera_evento_com_participante():
    texto = """
    PORTARIA GP Nº 23/2026
    DISPENSAR, CHRISTIANNE RAQUEL TAVARES DE LIMA,
    matrícula nº 1.14140-6,
    da Gratificação de Gestão Escolar - GGE,
    de Orientador Pedagógico,
    Secretaria Municipal de Educação,
    com efeitos a partir de 02/01/2026.
    """

    metadados = {"tipo": "portaria"}

    eventos = extrair_eventos_bloco(
        metadados,
        texto,
        diario_id=3216,
        numero_bloco=5,
    )

    assert len(eventos) == 1

    evento = eventos[0]

    assert evento["tipo_evento"] == DISPENSA
    assert evento["numero_portaria_gp"] == "23/2026"
    assert evento["agente"]["nome"] == "CHRISTIANNE RAQUEL TAVARES DE LIMA"
    assert evento["participantes"] == [
        {
            "tipo": "PESSOA",
            "nome": "CHRISTIANNE RAQUEL TAVARES DE LIMA",
        }
    ]

def test_designar_gera_evento_com_participante_e_orgao():
    texto = """
    PORTARIA GP Nº 45/2026 – DESIGNAR,
    nos termos da Lei Complementar Municipal nº 182/2014 e alterações posteriores,
    ALESSANDRA SERRADO NEVES, matrícula nº 1.08856-5, para perceber a Gratificação
    de Gestão Escolar - GGE, de Orientador Pedagógico (Escola "B"), Símbolo GGE-3, Cód.
    40763, na Secretaria Municipal de Educação, com efeitos a partir de 02/01/2026
    (Memorando nº 30.920/2025).
    """

    metadados = {"tipo": "portaria"}

    eventos = extrair_eventos_bloco(
        metadados,
        texto,
        diario_id=3216,
        numero_bloco=9,
    )

    assert len(eventos) == 1

    evento = eventos[0]

    assert evento["tipo_evento"] == DESIGNACAO
    assert evento["agente"]["nome"] == "ALESSANDRA SERRADO NEVES"
    assert evento["participantes"] == [
        {
            "tipo": "PESSOA",
            "nome": "ALESSANDRA SERRADO NEVES",
        }
    ]
    assert evento["orgao"] == "Secretaria Municipal de Educação"
    assert evento["numero_portaria_gp"] == "45/2026"

def test_dispensa_extrai_cargo_de_gratificacao():
    texto = """PORTARIA GP Nº 23/2026 – DISPENSAR, CHRISTIANNE RAQUEL TAVARES DE LIMA,
    matrícula nº 1.14140-6, da Gratificação de Gestão Escolar - GGE,
    de Orientador Pedagógico (Escola "E") (Lei Complementar Municipal nº 182/2014
    e alterações posteriores), Símbolo GGE-3, Cód. 40768,
    da Secretaria Municipal de Educação, com efeitos a partir de 02/01/2026."""

    assert extrair_cargo(texto) == "Orientador Pedagógico"

def test_designacao_extrai_cargo_de_gratificacao():
    texto = """PORTARIA GP Nº 45/2026 – DESIGNAR,
    nos termos da Lei Complementar Municipal nº 182/2014 e alterações posteriores,
    ALESSANDRA SERRADO NEVES, matrícula nº 1.08856-5,
    para perceber a Gratificação de Gestão Escolar - GGE,
    de Orientador Pedagógico (Escola "B"), Símbolo GGE-3, Cód. 40763,
    na Secretaria Municipal de Educação, com efeitos a partir de 02/01/2026."""

    assert extrair_cargo(texto) == "Orientador Pedagógico"


def test_designacao_extrai_cargo_com_unidade_na_denominacao():
    texto = """PORTARIA GP Nº 46/2026 – DESIGNAR,
    nos termos da Lei Complementar Municipal nº 182/2014 e alterações posteriores,
    JANAINA DE OLIVEIRA LIOTÉRIO, matrícula nº 1.15338-2,
    para perceber a Gratificação de Gestão Escolar - GGE,
    de Diretor de Escola Municipal "B", Símbolo GGE-6, Cód. 40747,
    na Secretaria Municipal de Educação, com efeitos a partir de 02/01/2026."""

    assert extrair_cargo(texto) == 'Diretor de Escola Municipal "B"'

def test_dispensa_extrai_cargo_antes_da_fundamentacao_legal():
    texto = """PORTARIA GP Nº 24/2026 – DISPENSAR, MARIA TUANE FERNANDES DE OLIVEIRA,
    matrícula nº 1.15106-1, da Gratificação de Gestão Escolar - GGE,
    de Auxiliar de Direção de Escola Municipal "D" (Lei Complementar Municipal nº 182/2014
    e alterações posteriores), Símbolo GGE-1, Cód. 40758,
    da Secretaria Municipal de Educação, com efeitos a partir de 02/01/2026."""

    assert extrair_cargo(texto) == 'Auxiliar de Direção de Escola Municipal "D"'

def test_extrair_agente_publico_designar_com_matricula():
    texto = """PORTARIA GP Nº
323/2026 – DESIGNAR, nos termos da Lei Complementar Municipal nº 182/2014 e
alterações posteriores, JOSIANE MARINA SILVEIRA RODRIGUES TAYT-
SOHN, matrícula nº 1.08800-1, para perceber a Gratificação de Gestão Escolar - GGE, de
Auxiliar de Direção de Escola Municipal "E", Símbolo GGE-1, Cód. 40814, na Secretaria
Municipal de Educação, a partir de 04/03/2026 (Memorando nº 2.793/2026)."""

    resultado = extrair_agente_publico(texto)

    assert resultado is not None
    assert "JOSIANE MARINA SILVEIRA RODRIGUES" in resultado
    assert "TAYT-" in resultado
    assert "SOHN" in resultado


def test_designar_enumerada():
    texto = '''
    Art. 2º Designar os servidores estáveis abaixo relacionados para compor a referida Comissão,
    sem prejuízo de suas atribuições funcionais, sob a presidência do primeiro:
    I - Gean Fabrizio Teixeira de Almada. Mat. 1.07537-4
    II - Gustavo Passos dos Santos. Mat. 1.09169-8
    III - Marcela Félix da Silva. Mat. 1.12393-9
    '''
    from events import extrair_servidores_designados
    result = extrair_servidores_designados(texto)
    nomes = [p["nome"] for p in result]
    assert nomes == [
        "Gean Fabrizio Teixeira de Almada",
        "Gustavo Passos dos Santos",
        "Marcela Félix da Silva",
    ]

def test_designar_textual_com_virgula_e_e():
    texto = '''
    Art. 2º Designar para compor a Comissão de Processo Administrativo Disciplinar os servidores:
    Gean Fabrizio Teixeira de Almada. Mat. 1.07537-4, Gustavo Passos dos
    Santos. Mat. 1.09169-8. e Marcela Félix da Silva. Mat. 1.12393-9, para,
    sob a presidência do primeiro, realizar os trabalhos apurados...
    '''
    from events import extrair_servidores_designados
    result = extrair_servidores_designados(texto)
    nomes = [p["nome"] for p in result]
    assert nomes == [
        "Gean Fabrizio Teixeira de Almada",
        "Gustavo Passos dos Santos",
        "Marcela Félix da Silva",
    ]

def test_designar_textual_outro_nome():
    texto = '''
    Art. 2º Designar para compor a Comissão de Processo Administrativo Disciplinar os servidores:
    Gean Fabrizio Teixeira de Almada. Mat. 1.07537-4, Gustavo Passos dos
    Santos. Mat. 1.09169-8. e Vagner Machado Roberto. Mat. 1.1, para,
    sob a presidência do primeiro, realizar os trabalhos apurados...
    '''
    from events import extrair_servidores_designados
    result = extrair_servidores_designados(texto)
    nomes = [p["nome"] for p in result]
    assert nomes == [
        "Gean Fabrizio Teixeira de Almada",
        "Gustavo Passos dos Santos",
        "Vagner Machado Roberto",
    ]

def test_nomear_nao_afetado():
    texto = '''
    NOMEAR, os servidores GEAN FABRIZIO TEIXEIRA DE ALMADA, matrícula nº 1.07537-4, 
    GUSTAVO PASSOS DOS SANTOS, matrícula nº 1.09169-8 e MARCELA FÉLIX DA SILVA, 
    matrícula nº 1.12393-9, para exercer a função...
    '''
    from events import extrair_servidores_designados
    result = extrair_servidores_designados(texto)
    nomes = [p["nome"] for p in result]
    assert nomes == [
        "GEAN FABRIZIO TEIXEIRA DE ALMADA",
        "GUSTAVO PASSOS DOS SANTOS",
        "MARCELA FÉLIX DA SILVA",
    ]


def test_referencia_interna_a_portaria_gp_nao_cria_subevento():
    texto = """
    PORTARIA GP Nº 727/2026 – NOMEAR, o servidor BERNARDO DA SILVA
    ARAÚJO DE OLIVEIRA, em substituição à servidora CLARISSA RIPPEL,
    nomeada mediante Portaria GP nº 1.516/2025 e alterada pela Portaria GP
    nº 1.264/2025, para exercer o Cargo em Comissão de Diretor, lotado na
    Secretaria Municipal de Administração.
    """

    subeventos = segmentar_sub_eventos(texto)

    assert len(subeventos) == 1
    assert "Secretaria Municipal de Administração" in subeventos[0]


def test_referencia_interna_a_portaria_gp_com_numero_nao_cria_subevento():
    texto = """
    PORTARIA GP Nº 681/2026 – NOMEAR, a servidora ANA DA SILVA,
    em substituição ao servidor BRUNO DA SILVA, nomeado anteriormente
    mediante Portaria GP nº 140/2026, como responsável pelo acompanhamento
    e fiscalização do Contrato nº 014.008.2025, firmado entre o Município
    de Teresópolis através da Secretaria Municipal de Assistência Social e
    Direitos Humanos e a Empresa XPTO Ltda.
    """

    subeventos = segmentar_sub_eventos(texto)

    assert len(subeventos) == 1
    assert (
        "Secretaria Municipal de Assistência Social e Direitos Humanos"
        in " ".join(subeventos[0].split())
    )
