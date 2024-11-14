using System;
using System.Linq;  // Importar LINQ
using Microsoft.EntityFrameworkCore;
using Microsoft.AspNetCore.Builder;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.AspNetCore.Http;
using System.ComponentModel.DataAnnotations;


var builder = WebApplication.CreateBuilder(args);


// Configuración de la conexión a PostgreSQL
var connectionString = "Host=db;Database=votesdb;Username=postgres;Password=password";
builder.Services.AddDbContext<VotingDbContext>(options =>
    options.UseNpgsql(connectionString));


// Configuración de la aplicación
var app = builder.Build();


// Endpoint para recibir y registrar el voto
app.MapPost("/vote", async (VotingDbContext dbContext, VoteRequest voteRequest) =>
{
    // Log para depurar la recepción de datos
    Console.WriteLine($"Voto recibido para MovieId: {voteRequest.MovieId}");


    // Verificar si el MovieId es válido
    if (voteRequest.MovieId == null)
    {
        return Results.BadRequest("Movie ID is required.");
    }


    // Guardar el voto en la base de datos
    var vote = new Vote { MovieId = voteRequest.MovieId, CreatedAt = DateTime.UtcNow };
    await dbContext.Votes.AddAsync(vote);
    await dbContext.SaveChangesAsync();


    return Results.Ok($"Vote for movie {voteRequest.MovieId} has been saved.");
});


// Endpoint para obtener las películas más votadas
app.MapGet("/top-votes", async (VotingDbContext dbContext) =>
{
    var topVotedMovies = await dbContext.Votes
        .GroupBy(v => v.MovieId)
        .OrderByDescending(g => g.Count())
        .Take(5)
        .Select(g => g.Key)
        .ToListAsync();




    return Results.Ok(topVotedMovies);
});


app.Run();


// Modelo de solicitud de voto
public class VoteRequest
{
    public int? MovieId { get; set; }
}


// Modelo de voto
public class Vote
{
    [Key]
    public int Id { get; set; }
    public int? MovieId { get; set; }
    public DateTime CreatedAt { get; set; }
}


// Contexto de la base de datos
public class VotingDbContext : DbContext
{
    public VotingDbContext(DbContextOptions<VotingDbContext> options) : base(options) { }
    public DbSet<Vote> Votes => Set<Vote>();
