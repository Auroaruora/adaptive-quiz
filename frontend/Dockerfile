# syntax=docker/dockerfile:1
#
# Frontend image: the Next.js standalone server. `output: "standalone"` in
# next.config.ts makes the build trace which files each route needs, so the
# final stage carries those files and nothing else from node_modules.
#
# NEXT_PUBLIC_API_URL is inlined into the browser bundle at build time, so
# it is a build argument here, not a runtime variable. It must be the URL
# the *browser* can reach, not the compose-internal service name.

FROM node:24-alpine AS deps

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci


FROM node:24-alpine AS builder

WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Declared after the copy so a changed URL rebuilds only from here.
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL} \
    NEXT_TELEMETRY_DISABLED=1

RUN npm run build


FROM node:24-alpine AS runner

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    HOSTNAME=0.0.0.0 \
    PORT=3000

RUN addgroup --system --gid 1001 nodejs \
    && adduser --system --uid 1001 --ingroup nodejs nextjs

WORKDIR /app

# server.js only serves .next/static when it sits beside it; the build
# leaves it outside the standalone folder because a CDN would normally
# take it. There is no public/ directory in this project to copy.
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

CMD ["node", "server.js"]
