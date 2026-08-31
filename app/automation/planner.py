from app.automation.models import Workflow, WorkflowStep, WorkflowStatus


class WorkflowPlanner:

    def get_ready_steps(self, workflow: Workflow) -> list[WorkflowStep]:
        """
        Retorna todas as etapas que podem ser executadas.
        """

        ready_steps = []

        for step in workflow.steps:

            # Ignora etapas que já foram executadas ou estão em execução
            if step.status != WorkflowStatus.PENDING:
                continue

            # Sem dependências: pode executar imediatamente
            if not step.depends_on:
                ready_steps.append(step)
                continue

            # Verifica se todas as dependências foram concluídas
            dependencies_completed = True

            for dependency in step.depends_on:

                dependency_step = next(
                    (s for s in workflow.steps if s.id == dependency),
                    None
                )

                if (
                    dependency_step is None or
                    dependency_step.status != WorkflowStatus.COMPLETED
                ):
                    dependencies_completed = False
                    break

            if dependencies_completed:
                ready_steps.append(step)

        return ready_steps