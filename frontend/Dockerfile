# Etapa 1: Construcción
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
# Construimos el proyecto Angular (creará la carpeta dist/)
RUN npm run build --configuration=production

# Etapa 2: Producción (Servidor SSR de Node)
FROM node:20-alpine
WORKDIR /app
# Copiamos la carpeta dist desde el builder
COPY --from=builder /app/dist ./dist
# Angular 17+ SSR suele correr desde un archivo server.mjs
# Ajusta el path exacto según cómo se llame tu proyecto en el angular.json
EXPOSE 4000
CMD ["node", "dist/frontend/server/server.mjs"]