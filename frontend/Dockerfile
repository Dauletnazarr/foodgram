# build env
FROM node:21.7.1-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install -g npm@latest
COPY . ./
RUN npm run build
CMD cp -r build result_build
