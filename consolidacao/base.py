"""Fluxo comum dos consolidadores, independente da entidade consolidada."""


def executar(conexao, carregar_grupos, persistir_grupo, preparar=None):
    """Executa o ciclo comum de uma consolidacao baseada em callbacks.

    O carregamento e a persistencia permanecem implementados pelo consolidador
    concreto para preservar o dialeto SQL e as regras da entidade.
    """
    if preparar is not None:
        preparar(conexao)

    grupos = carregar_grupos(conexao)
    for grupo in grupos:
        persistir_grupo(conexao, grupo)

    return len(grupos)
