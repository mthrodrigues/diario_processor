# Modelo de Domínio

## 1. Visão do Domínio

O sistema transforma Diários Oficiais em conhecimento estruturado.

Ele parte de documentos públicos originalmente dispersos em linguagem textual e converte essa matéria em unidades de informação que podem ser preservadas, relacionadas e consultadas com rastreabilidade. O valor do sistema não está apenas no armazenamento de texto, mas na capacidade de transformar uma publicação oficial em fatos administrativos reconhecíveis, entidades identificáveis e relações significativas.

O domínio, portanto, é o de uma base de inteligência documental pública: uma estrutura em que as evidências oficiais tornam-se ponto de partida para a construção de conhecimento.

## 2. Conceitos Fundamentais

### Documento

- Definição: o Diário Oficial, enquanto conjunto organizado de publicações oficiais.
- Identidade: é o recipiente de múltiplas ocorrências documentais.
- Responsabilidade: reunir as publicações que pertencem ao mesmo contexto formal de publicação.
- Ciclo de vida: nasce como uma fonte de publicação e permanece como referência histórica para as ocorrências que contém.

### Publicação

- Definição: a menor unidade documental relevante do sistema.
- Identidade: é uma ocorrência específica contida no Diário Oficial.
- Responsabilidade: preservar a evidência textual e os metadados locais da ocorrência.
- Ciclo de vida: surge com a publicação, recebe interpretação contextual e permanece como registro de referência.

### Evento

- Definição: um acontecimento institucional que pode ser inferido a partir de uma publicação.
- Identidade: é uma ocorrência com significado administrativo ou funcional.
- Responsabilidade: representar aquilo que aconteceu no domínio, como nomeação, exoneração, contratação ou designação.
- Ciclo de vida: emerge a partir da interpretação da publicação e passa a existir como fato reconhecido no sistema.

### Processo

- Definição: um objeto administrativo associado a uma tramitação ou procedimento.
- Identidade: é reconhecido por uma forma canônica que permite reuni-lo com outras ocorrências relacionadas.
- Responsabilidade: agrupar as publicações e eventos vinculados ao mesmo procedimento.
- Ciclo de vida: começa como uma referência presente em várias publicações e evolui para um catálogo consolidado.

### Contrato

- Definição: um instrumento administrativo relevante, geralmente associado a uma contratação ou formalização de compromisso.
- Identidade: é reconhecido por uma forma canônica própria.
- Responsabilidade: reunir as ocorrências relacionadas a um mesmo instrumento contratual.
- Ciclo de vida: surge como referência documental e se consolida em uma entidade administrativa independente.

### Pessoa

- Definição: um agente humano identificado em contextos institucionais.
- Identidade: é reconhecida por seu nome canônico.
- Responsabilidade: representar atores humanos em eventos e relacionamentos.
- Ciclo de vida: é criada a partir de uma menção documental e reutilizada em novos contextos.

### Empresa

- Definição: uma entidade jurídica privada ou empresarial associada a atos administrativos.
- Identidade: é reconhecida por sua forma canônica.
- Responsabilidade: representar fornecedores, contratadas e demais atores privados relevantes.
- Ciclo de vida: é identificada a partir do texto e reutilizada em diferentes publicações e eventos.

### Órgão

- Definição: uma entidade institucional pública.
- Identidade: é reconhecida por sua forma canônica.
- Responsabilidade: representar a estrutura administrativa envolvida em eventos e vínculos institucionais.
- Ciclo de vida: é identificado a partir das referências documentais e passa a servir como referência estável.

### Relacionamento

- Definição: uma conexão semântica entre entidades ou entre entidades e objetos administrativos.
- Identidade: é uma ligação com significado próprio, como participação, vinculação funcional ou associação contratual.
- Responsabilidade: expressar conhecimento derivado a partir dos fatos documentados.
- Ciclo de vida: nasce da interpretação de eventos e se mantém como registro de associação.

### Evidência

- Definição: o conteúdo textual original que sustenta qualquer interpretação posterior.
- Identidade: não é um conceito abstrato, mas a forma documental de prova.
- Responsabilidade: garantir que toda leitura do domínio tenha uma origem verificável.
- Ciclo de vida: acompanha a publicação e permanece como base para qualquer análise futura.

## 3. Fluxo Conceitual

O conhecimento surge progressivamente a partir das publicações oficiais.

```text
Diário Oficial
↓
Publicação
↓
Evento
↓
Processo / Contrato
↓
Entidades
↓
Relacionamentos
```

Esse fluxo mostra que o sistema não parte de uma visão abstrata pronta, mas de evidências documentais concretas. A partir delas, identifica-se o que aconteceu, a quem isso se refere e como esses elementos se relacionam.

## 4. Tipos de Entidades

O modelo distingue dois grandes tipos de entidades.

### Entidades nominativas

São as entidades que representam atores identificáveis no domínio:

- Pessoa
- Empresa
- Órgão

Essas entidades existem para nomear quem participa do cenário institucional.

### Objetos administrativos

São os conceitos que organizam a ação administrativa:

- Processo
- Contrato

Esses objetos não representam atores, mas instrumentos ou trâmites da gestão pública.

A diferença central é semântica: entidades nominativas identificam agentes; objetos administrativos organizam a ação e o registro formal.

## 5. Conhecimento Derivado

O modelo permite separar claramente três camadas de valor.

- Publicações preservam evidências.
- Entidades representam conceitos estáveis que dão identidade aos atores e instituições.
- Relacionamentos representam conhecimento derivado, ou seja, conexões interpretadas a partir das evidências.
- Eventos representam acontecimentos institucionalmente significativos.

Essa separação é essencial para manter a rastreabilidade do sistema e evitar confundir a prova documental com a interpretação que dela é feita.

## 6. Princípios do Modelo

Os princípios abaixo refletem a forma como o domínio foi estruturado.

- Evidência antes da interpretação: a publicação permanece como fonte primária.
- Identidade canônica: nomes e referências são normalizados para evitar duplicidade.
- Entidades enxutas: o modelo prioriza representações simples e estáveis dos atores.
- Consolidação: processos e contratos passam a existir como catálogos próprios.
- Rastreabilidade: toda interpretação pode ser vinculada à sua origem documental.
- Separação entre atores e objetos administrativos: pessoas, empresas e órgãos não são confundidos com processos e contratos.

## 7. Limites do Modelo

O modelo descrito aqui cobre o estado atual do sistema.

Ele inclui publicações, eventos, entidades nominativas, processos, contratos e relacionamentos, todos organizados a partir de evidências documentais preservadas. Ele não descreve funcionalidades futuras nem direções de evolução, mas apenas a estrutura conceitual atualmente adotada.
