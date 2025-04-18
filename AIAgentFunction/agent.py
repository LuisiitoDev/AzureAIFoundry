import os
from dotenv import load_dotenv
from typing import Any
from pathlib import Path
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import FunctionTool, ToolSet
from user_functions import user_functions



def main():
    # Clear the console
    os.system('cls' if os.name == 'nt' else 'clear')

    # Load environment variables from .env file
    load_dotenv()
    PROJECT_CONNECTION_STRING = os.getenv("AZURE_AI_AGENT_PROJECT_CONNECTION_STRING")
    MODEL_DEPLOYMENT = os.getenv("AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME")

    # Connect to the Azure AI Foundry project
    project_client = AIProjectClient.from_connection_string(
        credential=DefaultAzureCredential(
            exclude_environment_credential=True,
            exclude_managed_identity_credential=True
        ),
        conn_str=PROJECT_CONNECTION_STRING
    )

    # Define an agent that can use the custom functions
    with project_client:
        functions = FunctionTool(user_functions)
        toolset = ToolSet()
        toolset.add(functions)

        agent = project_client.agents.create_agent(
            model=MODEL_DEPLOYMENT,
            name="support-agent",
            instructions="""You are a technical support agent.
                            When a user has a technical issue, you get their email address and a description of the issue.
                            Then you use those values to submit a support ticket using the function available to you.
                            If a file is saved, tell the user the file name.
                        """,
            toolset=toolset
        )

        thread = project_client.agents.create_thread()
        print(f"You're chatting with: {agent.name} ({agent.id})")

        # Loop until the user types 'quit'
        while True:
            # Get input text
            user_prompt = input("Enter a prompt (or type 'quit' to exit): ")
            if user_prompt.lower() == "quit":
                break

            if len(user_prompt) == 0:
                print("Please enter a prompt.")
                continue

            # Send a prompt to the agent
            message = project_client.agents.create_message(
                thread_id=thread.id,
                role="user",
                content=user_prompt
            )
            run = project_client.agents.create_and_process_run(thread_id=thread.id, agent_id=agent.id)

            # Check the run status for failures
            if run.status == "failed":
                print(f"Run failed: {run.last_error}")

            # Show the latest response from the agent
            messages = project_client.agents.list_messages(thread_id=thread.id)
            last_msg = messages.get_last_text_message_by_role("assistant")
            if last_msg:
                print(f"Last Message: {last_msg.text.value}")

            # Get the conversation history
            print("\nConversation Log:\n")
            messages = project_client.agents.list_messages(thread_id=thread.id)
            for message_data in reversed(messages.data):
                last_message_content = message_data.content[-1]
                print(f"{message_data.role}: {last_message_content.text.value}\n")

        # Clean up - only after exiting the loop
        project_client.agents.delete_agent(agent.id)
        project_client.agents.delete_thread(thread.id)

if __name__ == '__main__':
    main()
