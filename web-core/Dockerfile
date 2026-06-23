# Etapa 1: Construcción (Build)
FROM maven:3.9.6-eclipse-temurin-17-alpine AS builder
WORKDIR /build
# Copiamos solo el pom.xml primero para aprovechar el caché de las dependencias
COPY ./v1/pom.xml .
# Descarga las dependencias de internet (esto se cachea si no modificas el pom)
RUN mvn dependency:go-offline
# Copiamos el código fuente
COPY ./v1/src ./src
# Compilamos el proyecto omitiendo los tests para acelerar el despliegue
RUN mvn clean package -DskipTests

# Etapa 2: Producción (Runtime)
FROM eclipse-temurin:17-jdk-alpine
WORKDIR /app
# Copiamos el .jar generado en la Etapa 1
COPY --from=builder /build/target/*.jar app.jar
EXPOSE 8080
# Comando optimizado de Java para contenedores (previene problemas de memoria)
CMD ["java", "-XX:+UseContainerSupport", "-XX:MaxRAMPercentage=75.0", "-jar", "app.jar"]