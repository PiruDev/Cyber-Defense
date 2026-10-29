
from agents import Agent, Runner

diretor = Agent(
    name="Diretor AgentOS",
    instructions=(
        "Voce e diretor de um estudio de desenvolvimento "
        "de jogos. Responda sempre em portugues."
    )
)

resultado = Runner.run_sync(
    diretor,
    "Apresente-se como diretor do AgentOS Game Studio."
)

print(resultado.final_output)
