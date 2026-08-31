from pathlib import Path
import sys

import pdfplumber

ROOT_DIR = Path(__file__).resolve().parent.parent

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from pot_extractor import (
    _agrupar_publicacoes_pot,
    _corrigir_coluna_numero_ausente_pot,
    _identificar_layout_tabela_pot,
    _eh_tabela_pot,
    _reconstruir_publicacoes_pot,
    _registro_pot_da_linha,
    extrair_publicacoes_pot_pdf,
    extrair_registros_pot_pdf,
)

from extractor import extrair_texto
from parser import segmentar_publicacoes, identificar_tipo


PDF_FIXTURE = (
    Path(__file__).parent
    / "fixtures"
    / "diario_3252.pdf"
)


def _abrir_pdf_fixture():
    return pdfplumber.open(PDF_FIXTURE)


def test_extrai_130_registros_pot():
    with _abrir_pdf_fixture() as pdf:
        registros = extrair_registros_pot_pdf(pdf)

    assert len(registros) == 130

def test_reconstroi_registro_4_na_quebra_p16_p17():
    with _abrir_pdf_fixture() as pdf:
        registros = extrair_registros_pot_pdf(pdf)

    encontrados = [
        registro
        for registro in registros
        if registro["beneficiario"]
        == "Maria Vanderleia Carreiro de Souza"
    ]

    assert len(encontrados) == 1

    registro = encontrados[0]

    assert registro["numero"] == "4"
    assert registro["unidade"] == "EM Fazenda Alpina"
    assert registro["area_aprendizado"] == "Apoio/Escolar"
    assert registro["data_inclusao"] == "04/02/2026"
    assert (
        registro["substituicao"]
        == "Jussara Carreiro de Barros "
        "(Desligada em 31/12/2025)"
    )


def test_reconstroi_registro_4_na_quebra_p17_p18():
    with _abrir_pdf_fixture() as pdf:
        registros = extrair_registros_pot_pdf(pdf)

    encontrados = [
        registro
        for registro in registros
        if registro["beneficiario"]
        == "Sabrina de Oliveira Ferreira"
    ]

    assert len(encontrados) == 1

    registro = encontrados[0]

    assert registro["numero"] == "4"
    assert registro["unidade"] == "CM Paraíso"
    assert registro["area_aprendizado"] == "Apoio/Creche"
    assert registro["data_inclusao"] == "05/03/2026"
    assert (
        registro["substituicao"]
        == "Tatiana de Souza Bianchini "
        "(desligada em 12/12/2025)"
    )

def test_extrai_pot_desligados_diario_3352():
    pdf_path = (
        Path(__file__).parent
        / "fixtures"
        / "diario_3352.pdf"
    )

    with pdfplumber.open(pdf_path) as pdf:
        registros = extrair_registros_pot_pdf(pdf)

    assert len(registros) == 1

    registro = registros[0]

    assert registro["numero"] == "1"
    assert registro["beneficiario"] == (
        "Nathalia dos\nSantos Bernabé"
    )
    assert registro["unidade"] == (
        "CM OSCAR\nLOBATO"
    )
    assert registro["horario_atuacao"] == (
        "07:00h às\n11:30h\n12:30h às\n16:00h"
    )
    assert registro["area_aprendizado"] == (
        "APOIO/ESCOLAR"
    )
    assert registro["data_inclusao"] is None
    assert registro["data_desligamento"] == "06/05/2026"
    assert registro["substituicao"] is None


def test_extrai_pot_desligados_diario_3431():
    pdf_path = (
        Path(__file__).parent
        / "fixtures"
        / "diario_3431.pdf"
    )

    with pdfplumber.open(pdf_path) as pdf:
        registros = extrair_registros_pot_pdf(pdf)

    assert len(registros) == 5

    assert [registro["numero"] for registro in registros] == [
        "1",
        "2",
        "3",
        "4",
        "5",
    ]

    assert registros[0]["beneficiario"] == (
        "Fernanda\nMaurat Medeiros"
    )

    assert registros[3]["beneficiario"] == (
        "Joelma de\nSouza Cruz"
    )

    assert registros[4]["beneficiario"] == (
        "Leticia da Cruz\nAlbuquerque"
    )

    assert registros[4]["data_desligamento"] == "21/08/2026"

def test_estrutura_publicacoes_pot_preserva_fronteiras_fisicas():
    casos = [
        (
            "diario_3252.pdf",
            [
                [
                    [1, 2, 3, 4, 5, 6, 7, 8, 9],
                    [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
                    [21, 22, 23, 24, 25, 26, 27, 28, 29, 30],
                    [31, 32, 33, 34, 35, 36, 37, 38, 39, 40],
                    [41, 42, 43, 44, 45, 46, 47],
                    [48, 49, 50, 51, 52, 53, 54, 55, 56, 57],
                    [58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68],
                    [69, 70, 71, 72, 73, 74, 75, 76, 77, 78],
                    [79, 80, 81, 82, 83, 84, 85, 86, 87, 88],
                    [89, 90, 91, 92, 93, 94, 95, 96, 97, 98],
                    [99, 100, 101, 102, 103, 104],
                ],
                [
                    [1, 2],
                    [3, 4, 5, 6],
                ],
                [
                    [1, 2, 3],
                    [4, 5, 6],
                ],
                [
                    [1, 2, 3],
                    [4, 5, 6, 7, 8, 9, 10, 11, 12],
                    [13, 14],
                ],
            ],
        ),
        (
            "diario_3352.pdf",
            [
                [
                    [1],
                ],
            ],
        ),
        (
            "diario_3431.pdf",
            [
                [
                    [1, 2, 3, 4],
                    [5],
                ],
            ],
        ),
    ]

    for nome_pdf, sequencias_esperadas in casos:
        pdf_path = (
            Path(__file__).parent
            / "fixtures"
            / nome_pdf
        )

        with pdfplumber.open(pdf_path) as pdf:
            publicacoes_pot = _agrupar_publicacoes_pot(pdf)

        estrutura_obtida = []

        for grupo in publicacoes_pot:
            tabelas_grupo = []

            for tabela in grupo:
                numeros = []

                for registro in tabela["registros"]:
                    numero = registro.get("numero")

                    if numero is None:
                        continue

                    numeros.append(int(numero))

                tabelas_grupo.append(numeros)

            estrutura_obtida.append(tabelas_grupo)

        assert estrutura_obtida == sequencias_esperadas, nome_pdf

def test_quantidade_publicacoes_pot_bate_com_segmentacao():
    casos = [
        ("diario_3252.pdf", 4),
        ("diario_3352.pdf", 1),
        ("diario_3431.pdf", 1),
    ]

    for nome_pdf, quantidade_esperada in casos:
        pdf_path = (
            Path(__file__).parent
            / "fixtures"
            / nome_pdf
        )

        texto = extrair_texto(str(pdf_path))
        blocos = segmentar_publicacoes(texto)

        blocos_pot = [
            bloco
            for bloco in blocos
            if identificar_tipo(bloco) == "pot"
        ]

        with pdfplumber.open(pdf_path) as pdf:
            publicacoes_pot = _agrupar_publicacoes_pot(pdf)

        assert len(blocos_pot) == quantidade_esperada
        assert len(publicacoes_pot) == quantidade_esperada

def test_reconstrucao_publicacoes_pot_produz_tamanhos_logicos():
    casos = [
        (
            "diario_3252.pdf",
            [104, 6, 6, 14],
        ),
        (
            "diario_3352.pdf",
            [1],
        ),
        (
            "diario_3431.pdf",
            [5],
        ),
    ]

    for nome_pdf, tamanhos_esperados in casos:
        pdf_path = (
            Path(__file__).parent
            / "fixtures"
            / nome_pdf
        )

        with pdfplumber.open(pdf_path) as pdf:
            grupos_fisicos = _agrupar_publicacoes_pot(pdf)
            grupos_logicos = _reconstruir_publicacoes_pot(
                grupos_fisicos
            )

        assert [
            len(grupo)
            for grupo in grupos_logicos
        ] == tamanhos_esperados, nome_pdf

def test_extrai_publicacoes_pot_agrupadas():
    casos = [
        ("diario_3252.pdf", [104, 6, 6, 14]),
        ("diario_3352.pdf", [1]),
        ("diario_3431.pdf", [5]),
    ]

    for nome_pdf, tamanhos_esperados in casos:
        pdf_path = (
            Path(__file__).parent
            / "fixtures"
            / nome_pdf
        )

        with pdfplumber.open(pdf_path) as pdf:
            publicacoes = extrair_publicacoes_pot_pdf(pdf)

        assert [
            len(publicacao)
            for publicacao in publicacoes
        ] == tamanhos_esperados, nome_pdf

def test_extrai_numero_pot_contaminado_na_coluna():
    assert _registro_pot_da_linha(
        [
            "I\n3",
            "ngrid Dias de\nOliveira",
            "EM BELKIS\nFRONY\nMORGADO",
            "07:30h às\n11:30h\n13:00h às\n17:00h",
            "APOIO/CUIDADOR(A)",
            "18/08/2026",
        ],
        "desligado",
    )["numero"] == "3"

def test_extrai_numero_pot_com_fragmentos_da_coluna_beneficiario():
    casos = [
        ("S\n1\nd", "1"),
        ("2 J", "2"),
        ("3 J\nP", "3"),
        ("4\nA", "4"),
        ("V\n5\nS", "5"),
        ("6\nL", "6"),
        ("L\n7", "7"),
        ("B\n8", "8"),
    ]

    for valor, esperado in casos:
        registro = _registro_pot_da_linha(
            [
                valor,
                "Beneficiário",
                "Unidade",
                "07:00h às\n13:00h",
                "APOIO/ESCOLAR",
                "17/07/2026",
            ],
            "desligado",
        )

        assert registro["numero"] == esperado

def test_agrupar_publicacoes_pot_3396_preserva_duas_publicacoes():
    pdf_path = (
        Path(__file__).parent
        / "fixtures"
        / "diario_3396.pdf"
    )

    with pdfplumber.open(pdf_path) as pdf:
        grupos = _agrupar_publicacoes_pot(pdf)

    assert len(grupos) == 2

    assert [
        sum(
            1
            for tabela in grupo
            for registro in tabela["registros"]
            if registro.get("numero") is not None
        )
        for grupo in grupos
    ] == [1, 16]

def test_reconstruir_publicacoes_pot_3396():
    pdf_path = (
        Path(__file__).parent
        / "fixtures"
        / "diario_3396.pdf"
    )

    with pdfplumber.open(pdf_path) as pdf:
        grupos = _agrupar_publicacoes_pot(pdf)

    publicacoes = _reconstruir_publicacoes_pot(grupos)

    assert [
        len(publicacao)
        for publicacao in publicacoes
    ] == [1, 16]

def test_agrupar_publicacoes_pot_3430_reconhece_numero_3():
    pdf_path = (
        Path(__file__).parent
        / "fixtures"
        / "diario_3430.pdf"
    )

    with pdfplumber.open(pdf_path) as pdf:
        grupos = _agrupar_publicacoes_pot(pdf)

    registros = [
        registro
        for grupo in grupos
        for tabela in grupo
        for registro in tabela["registros"]
    ]

    encontrados = [
        registro
        for registro in registros
        if registro["beneficiario"]
        and "ngrid Dias" in registro["beneficiario"]
    ]

    assert len(encontrados) == 1
    assert encontrados[0]["numero"] == "3"

def test_reconstroi_beneficiario_afetado_pela_fronteira_da_coluna_numero():
    casos = [
        (
            "S\n1\nd",
            "amanta Pires\ne Almeida",
            "Samanta Pires de Almeida",
        ),
        (
            "2 J",
            "Mariane de\nesús da Silva\nCandido",
            "Mariane de Jesús da Silva Candido",
        ),
        (
            "3 J\nP",
            "Romulo\nunqueira\nrado Júnior",
            "Romulo Junqueira Prado Júnior",
        ),
        (
            "4\nA",
            "Wesley de\nlmeida Lopes",
            "Wesley de Almeida Lopes",
        ),
        (
            "V\n5\nS",
            "ictor\nNascimento da\nilva",
            "Victor Nascimento da Silva",
        ),
        (
            "L\n7",
            "ucimar de\nOliveira Matos",
            "Lucimar de Oliveira Matos",
        ),
        (
            "B\n8",
            "etina\nRodrigues\nCarneiro",
            "Betina Rodrigues Carneiro",
        ),
    ]

    for numero_raw, beneficiario_raw, esperado in casos:
        registro = _registro_pot_da_linha(
            [
                numero_raw,
                beneficiario_raw,
                "Unidade",
                "07:00h às\n13:00h",
                "APOIO/ESCOLAR",
                "17/07/2026",
            ],
            "desligado",
        )

        assert registro["beneficiario"] == esperado

def test_identifica_tabela_pot_com_cabecalho_local_de_trabalho():
    dados = [
        [
            "Nº",
            "Beneficiário(s)",
            "Local de\nTrabalho\n(Unidade\nEscolar)",
            "Horário\nde\nTrabalho",
            "Área de Aprendizado",
            "Data de\nDesligamento",
        ]
    ]

    assert _eh_tabela_pot(dados) is True
    assert _identificar_layout_tabela_pot(dados) == "desligado"

def test_identifica_tabela_pot_com_cabecalho_dividido_em_duas_linhas():
    dados = [
        [
            "",
            "",
            "Local de\nAtuação",
            "Horário",
            "Área de",
            "Data de",
        ],
        [
            "Nº",
            "Beneficiário(s)",
            "(Unidade\nEscolar)",
            "de\nAtuação",
            "Aprendizado",
            "Desligamento",
        ],
        [
            "1",
            "Adriana Lopes\nMiranda",
            "CMEI PROFº\nJOSÉ MARIA\nLEITÃO\nCARNEIRO",
            "08:20h\nàs\n12:20h\n13:20h\nàs\n17:20h",
            "APOIO/ESCOLAR",
            "19/05/2026",
        ],
    ]

    assert _eh_tabela_pot(dados) is True
    assert _identificar_layout_tabela_pot(dados) == "desligado"

def test_corrige_coluna_numero_ausente_na_tabela_pot():
    dados = [
        [
            "Beneficiário(s)",
            "Local de\nAtuação\n(Unidade\nEscolar)",
            "Horário\nde\nAtuação",
            "Área de\nAprendizado",
            "Data de\nDesligamento",
        ],
        [
            "Kesia Murtha\nSantana",
            "CM\nCOMEÇANDO A",
            "07:30h às\n12:10h",
            "APOIO/CRECHE",
            "10/07/2026",
        ],
    ]

    corrigidos = _corrigir_coluna_numero_ausente_pot(dados)

    assert corrigidos[0][0] == ""
    assert corrigidos[0][1] == "Beneficiário(s)"
    assert corrigidos[1][0] == ""
    assert corrigidos[1][1] == "Kesia Murtha\nSantana"

def test_reconstrui_continuacao_final_sem_numero():
    grupos = [
        [
            {
                "pagina": 3,
                "tabela": 0,
                "layout": "desligado",
                "registros": [
                    {
                        "numero": "1",
                        "beneficiario": "Kesia Murtha Santana",
                        "unidade": "CM COMEÇANDO A",
                        "horario_atuacao": "07:30h às 12:10h",
                        "area_aprendizado": "APOIO/CRECHE",
                        "data_desligamento": "10/07/2026",
                    }
                ],
            },
            {
                "pagina": 4,
                "tabela": 0,
                "layout": "desligado",
                "registros": [
                    {
                        "numero": None,
                        "beneficiario": None,
                        "unidade": "VIVER",
                        "horario_atuacao": "13:10h às 16:30h",
                        "area_aprendizado": None,
                        "data_desligamento": None,
                    }
                ],
            },
        ]
    ]

    publicacoes = _reconstruir_publicacoes_pot(grupos)

    assert len(publicacoes) == 1
    assert len(publicacoes[0]) == 1

    registro = publicacoes[0][0]

    assert registro["numero"] == "1"
    assert registro["beneficiario"] == "Kesia Murtha Santana"
    assert registro["unidade"] == "CM COMEÇANDO A VIVER"
    assert registro["horario_atuacao"] == (
        "07:30h às 12:10h 13:10h às 16:30h"
    )

def test_agrupar_publicacoes_pot_3328_separa_inicio_sem_numero():
    pdf_path = (
        Path(__file__).parent
        / "fixtures"
        / "diario_3328.pdf"
    )

    with pdfplumber.open(pdf_path) as pdf:
        grupos = _agrupar_publicacoes_pot(pdf)

    assert len(grupos) == 2

    assert [
        sum(
            len(tabela["registros"])
            for tabela in grupo
        )
        for grupo in grupos
    ] == [18, 56]

    assert (
        grupos[1][0]["registros"][0]["beneficiario"]
        == "Eni Reis Jardim"
    )

    assert (
        grupos[1][1]["registros"][0]["numero"]
        == "1"
    )

def test_reconstruir_publicacoes_pot_3328_reconstroi_eni_reis():
    pdf_path = (
        Path(__file__).parent
        / "fixtures"
        / "diario_3328.pdf"
    )

    with pdfplumber.open(pdf_path) as pdf:
        grupos = _agrupar_publicacoes_pot(pdf)
        publicacoes = _reconstruir_publicacoes_pot(
            grupos
        )

    assert len(publicacoes) == 2

    primeiro = publicacoes[1][0]

    assert primeiro["numero"] == "1"
    assert primeiro["beneficiario"] == (
        "Eni Reis Jardim Sobrinho"
    )

def test_agrupar_publicacoes_pot_3328_separa_inicio_sem_numero():
    pdf_path = (
        Path(__file__).parent
        / "fixtures"
        / "diario_3328.pdf"
    )

    with pdfplumber.open(pdf_path) as pdf:
        grupos = _agrupar_publicacoes_pot(pdf)

    assert len(grupos) == 2

    assert [
        [
            (tabela["pagina"], tabela["tabela"])
            for tabela in grupo
        ]
        for grupo in grupos
    ] == [
        [
            (4, 0),
            (5, 0),
        ],
        [
            (5, 1),
            (6, 0),
            (7, 0),
            (8, 0),
            (9, 0),
            (10, 0),
            (11, 0),
        ],
    ]