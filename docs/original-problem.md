Operação Resgate Espacial


1. O sinal de emergência

Uma tempestade solar está a caminho da estação Aurora. Os escudos não vão resistir, e as pessoas a bordo precisam de transporte para sair de lá. A quantidade de pessoas a evacuar deve ser informada como entrada de cada missão.

Há naves nas proximidades, com diferentes capacidades e tempos de chegada. A central precisa coordenar a ajuda dos comandantes: alguns confirmam todas as vagas solicitadas, outros oferecem apenas parte delas, e outros recusam. Nem todos respondem na mesma hora.

Sua missão: construir o sistema da central de resgate, distribuindo pedidos entre as naves e acompanhando as confirmações até garantir um assento para cada pessoa.

 

2. O problema da central

Hoje, a equipe coordena o resgate pelo rádio e registra as respostas em uma planilha. Com vários operadores trabalhando ao mesmo tempo, é difícil saber se ainda falta pedir ajuda, se basta aguardar as respostas ou se o transporte de todos já está garantido.

Mobilizar naves além do necessário pode prejudicar outros resgates. Por outro lado, contar com vagas que ninguém confirmou pode deixar pessoas para trás. A central precisa de informações confiáveis para tomar essas decisões.

O escopo termina na confirmação das reservas. Não é necessário simular voos, embarques, rotas ou a tempestade solar.

 

3. O que o sistema deve fazer

3.1 Receber uma missão de resgate

Permitir cadastrar uma missão, identificando a estação e a quantidade de pessoas que precisam de transporte. A central também recebe informações sobre as naves disponíveis, incluindo a capacidade oferecida e o tempo estimado de chegada.

3.2 Acompanhar o resgate

Permitir que um operador consulte a situação da missão e dos pedidos enviados às naves. As informações apresentadas devem ajudá-lo a entender o que já está garantido, o que ainda depende de resposta e se é necessário buscar mais ajuda. Defina como representar e apresentar esse acompanhamento.

3.3 Coordenar os pedidos

Enviar pedidos de vagas às naves e processar suas respostas. Uma nave pode confirmar toda a quantidade solicitada, confirmar apenas parte dela ou recusar. Uma confirmação parcial encerra a resposta daquele pedido: a central precisará buscar em outro pedido as vagas que não foram confirmadas.

Também deve ser possível cancelar um pedido ainda sem resposta ou encerrá-lo por falta de resposta. O sistema deve permitir continuar a mobilização quando a ajuda obtida não for suficiente.

 

4. Compromissos da central

Evitar pedidos em excesso. Ao solicitar novas vagas, a central precisa considerar tanto as confirmações recebidas quanto os pedidos que ainda podem ser aceitos.
Concluir com segurança. A reserva de transporte só está completa quando há vagas confirmadas para todas as pessoas da missão.
Respeitar o que foi solicitado. Uma nave não pode confirmar mais vagas do que recebeu no pedido. Quantidades informadas devem ser válidas para o contexto.
Preservar decisões encerradas. Depois de respondido, cancelado ou expirado, um pedido não pode ter seu resultado alterado por uma nova resposta.
Manter informações confiáveis. Mensagens repetidas, atrasadas ou fora de ordem e operações simultâneas não podem distorcer o andamento do resgate. Operações inválidas não devem comprometer os dados já registrados.
As escolhas de modelagem e os mecanismos usados para cumprir esses compromissos fazem parte da solução.

 

5. Estratégia de mobilização

Cabe ao sistema decidir quais naves acionar e quantas vagas pedir a cada uma, considerando as informações disponíveis e as regras da missão.

Defina e implemente uma estratégia. Explique no README os critérios escolhidos, as premissas assumidas e como sua solução lida com mudanças de disponibilidade ao longo do resgate.

 

6. Demonstração da solução

Prepare uma demonstração em que a missão precise da ajuda de várias naves. Durante a mobilização, uma delas confirma menos vagas do que o solicitado e outra recusa. A central deve conseguir acompanhar a situação e buscar a ajuda que ainda falta.

Escolha os dados da demonstração e os cenários de teste. Mostre como você verifica que a solução cumpre os compromissos da central, inclusive quando a comunicação não acontece como esperado.

 

7. Requisitos técnicos e limites do exercício

Linguagem à sua escolha (Java, Python, C#, TypeScript…).
A persistência pode ser em memória.
Não é obrigatório criar interface gráfica, API HTTP, serviço de mensagens ou integração externa. Chamadas de métodos e simulações são suficientes.
Envios de pedidos e respostas das naves podem ocorrer em paralelo. Explique, ou implemente, como você garante a consistência nessas situações.
Cancelamento e expiração podem ser simulados. Não é necessário implementar temporizadores reais.
Capacidades e estimativas de chegada podem ser fornecidas como dados de entrada. O controle global da frota entre diferentes missões fica fora do escopo.
Você pode usar ferramentas de IA (ChatGPT, Copilot, Claude etc.) para resolver o exercício. Esteja preparado para explicar suas decisões e o funcionamento da solução entregue.
 

8. Entregáveis

Código-fonte em repositório Git ou arquivo compactado.
Testes automatizados cobrindo os cenários que você considera relevantes.
README com instruções para executar a demonstração e os testes, decisões de design e premissas assumidas.
 

9. Diferenciais

Incentivamos que você vá além do que foi pedido, com funcionalidades extras que façam sentido para o problema.

Alguma ambiguidade? Assuma o que fizer mais sentido e registre a premissa no README. Queremos entender como você transforma as necessidades da central em uma solução e como sustenta suas decisões.