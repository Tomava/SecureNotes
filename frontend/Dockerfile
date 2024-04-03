FROM node:20.11

RUN mkdir /app

WORKDIR /app

COPY . .

RUN chown -R node:node /app

USER node

RUN npm install

EXPOSE 3000

RUN npm run build

CMD ["npm", "start"]
