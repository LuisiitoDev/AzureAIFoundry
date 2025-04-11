// Add references
using Azure.Identity;
using Azure.AI.Projects;
using Azure.AI.Inference;
using Microsoft.Extensions.Configuration;

Console.Clear();

var builder = new ConfigurationBuilder()
    .AddJsonFile("appsettings.json")
    .AddUserSecrets<Program>();

var configuration = builder.Build();

var project_connection = configuration["ProjectConnection"];
var model_deployment = configuration["ModelDeployment"];

var projectClient = new AIProjectClient(connectionString: project_connection, new DefaultAzureCredential());
var chat = projectClient.GetChatCompletionsClient();

var prompt = new List<ChatRequestMessage>()
{
    new ChatRequestSystemMessage("You are a helpful AI assistant that answers questions.")
};

string user_prompt = string.Empty;

while(!IsQuit(user_prompt))
{
    Console.WriteLine("Enter your prompt (or type 'quit' to exit.)");
    user_prompt = Console.ReadLine()!;

    if (IsQuit(user_prompt)) break;

    prompt.Add(new ChatRequestUserMessage(user_prompt));

    var response = chat.Complete(new ChatCompletionsOptions
    {
        Model = model_deployment,
        Messages = prompt,
    });

    var completation = response.Value.Content;
    Console.WriteLine($"AI: {completation}");
    prompt.Add(new ChatRequestAssistantMessage(completation));
}

static bool IsQuit(string value)
{
    return value.Equals("quit", StringComparison.CurrentCultureIgnoreCase);
}