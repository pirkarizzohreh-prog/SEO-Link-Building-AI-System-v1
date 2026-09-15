FROM node:22-slim

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
# NEXT_PUBLIC_* vars are baked in at build time, not read at container
# start — pass it as a build arg so a real deploy can point at its API.
ARG NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
RUN npm run build

EXPOSE 3000
CMD ["npm", "start"]
