# Frontend image for production (Next.js, standalone output).
# Build context: the frontend/ folder.
#   docker build --build-arg NEXT_PUBLIC_API_URL=https://api.example.com -t omnilog-frontend ./frontend
#
# NEXT_PUBLIC_API_URL is written into the JavaScript at build time (Next.js does this for every
# NEXT_PUBLIC_ variable). Changing the API address means building the image again.

FROM node:24-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM node:24-alpine AS build
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1
COPY --from=deps /app/node_modules ./node_modules
COPY . .

ARG NEXT_PUBLIC_API_URL
# Stop early. Without the address the browser would call http://localhost:8000
RUN test -n "$NEXT_PUBLIC_API_URL" || (echo "Build argument NEXT_PUBLIC_API_URL is required" && exit 1)
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
RUN npm run build

FROM node:24-alpine AS runtime
WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0

RUN addgroup -S -g 10001 nextjs && adduser -S -u 10001 -G nextjs nextjs

# The standalone folder has the server and only the files it needs. The static files and the
# public folder are not copied into it by Next.js, so they are copied here.
COPY --from=build --chown=nextjs:nextjs /app/.next/standalone ./
COPY --from=build --chown=nextjs:nextjs /app/.next/static ./.next/static
COPY --from=build --chown=nextjs:nextjs /app/public ./public

USER 10001
EXPOSE 3000

HEALTHCHECK --interval=10s --timeout=5s --start-period=20s --retries=5 \
    CMD ["wget", "-q", "-O", "/dev/null", "http://127.0.0.1:3000/"]

CMD ["node", "server.js"]