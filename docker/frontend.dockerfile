# frontend.dockerfile
FROM node:18-alpine
WORKDIR /app

COPY ./frontend/package*.json ./
RUN npm install

COPY ./frontend ./

# 개발 환경
CMD ["npm", "run", "dev"]

# 프로덕션 환경 (필요시 주석 해제)
# RUN npm run build
# CMD ["npx", "serve", "-s", "out", "-l", "3000"]