# Etapa 1: Construcción
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /app


# Copiar y restaurar las dependencias
COPY *.csproj ./
RUN dotnet restore


# Copiar el resto de los archivos y construir la aplicación
COPY . ./
RUN dotnet publish -c Release -o /out


# Etapa 2: Ejecución
FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS runtime
WORKDIR /app
COPY --from=build /out .


# Configurar la aplicación para escuchar en todos los puertos
ENV ASPNETCORE_URLS=http://+:8080
EXPOSE 8080


# Ejecutar la aplicación
ENTRYPOINT ["dotnet", "worker.dll"]