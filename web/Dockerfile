# Imagen de la web: se compila con Node y se sirve con nginx.
# Dos etapas: la imagen final solo lleva los archivos estáticos (sin Node ni
# node_modules), así pesa ~50 MB en vez de ~500 MB.

# --- Etapa 1: compilar ---
FROM node:22-alpine AS compilar
WORKDIR /web
# Dependencias primero: esta capa queda en caché mientras no cambie package-lock.
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

# --- Etapa 2: servir ---
FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=compilar /web/dist /usr/share/nginx/html
EXPOSE 80
