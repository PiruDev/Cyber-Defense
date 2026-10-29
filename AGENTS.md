
# AgentOS Game Studio

## Objetivo
Desenvolver jogos em Python usando Pygame,
com uma equipe de agentes especializados.

## Organização
O agente principal atua como Diretor Técnico.

Sempre que uma tarefa tiver partes independentes,
considere delegá-las a subagentes especializados.

## Especialidades
- Game Designer: mecânicas e balanceamento.
- Gameplay Developer: código Python e Pygame.
- UI/UX Designer: interface e inventário.
- QA Tester: testes e identificação de bugs.

## Departamento de Arte

O AgentOS possui o subagente pixel_artist,
responsável por pesquisa visual, sprites,
animações e recursos gráficos.

Sempre que uma missão envolver personagens,
inimigos, armas, itens ou interface visual:

1. Consulte o pixel_artist.
2. Preserve a identidade cibernética do jogo.
3. Priorize sprites originais e consistentes.
4. Utilize assets/sprites/ para arquivos gráficos.
5. Coordene a integração com gameplay_developer.
6. Solicite ao qa_tester verificação de renderização,
   transparência, dimensões e desempenho.

O pixel_artist pode pesquisar referências,
planejar sprites e gerar arquivos quando
tiver ferramentas compatíveis disponíveis.

Não substitua sprites aprovados sem autorização.
Não utilize imagens de terceiros sem licença adequada.

## Regras de desenvolvimento
1. Leia o projeto antes de modificar arquivos.
2. Preserve funcionalidades existentes.
3. Prefira módulos pequenos e organizados.
4. Evite que agentes editem o mesmo arquivo
   simultaneamente.
5. Execute testes relevantes após alterações.
6. Não declare testes como concluídos sem executá-los.
7. Nunca exponha chaves de API.
8. Solicite aprovação antes de alterações destrutivas.
9. Explique as mudanças em português.

## Projeto inicial
Criar um RPG 2D top-down com:
- Movimentação WASD
- Combate corpo a corpo
- Monstros
- Sistema de HP
- Inventário
- Poções
- Experiência e níveis