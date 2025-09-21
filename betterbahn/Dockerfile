# base image
FROM node:24-alpine AS base
# set pnpm home
ENV PNPM_HOME="/pnpm"
# add pnpm to path
ENV PATH="$PNPM_HOME:$PATH"
# enable corepack
RUN corepack enable

# dependency installation stage
FROM base AS deps
# set working directory
WORKDIR /app

# copy package files
COPY package.json pnpm-lock.yaml ./
# install dependencies
RUN pnpm install

# builder stage
FROM base AS builder
# set working directory
WORKDIR /app
# copy node_modules from deps stage
COPY --from=deps /app/node_modules ./node_modules
# copy source code
COPY . .
# build application
RUN pnpm run build

# final runner stage
FROM base AS runner
# set working directory
WORKDIR /app

# set production environment
ENV NODE_ENV=production
# disable next.js telemetry
ENV NEXT_TELEMETRY_DISABLED=1

# copy standalone output from builder stage
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

# manually copy module data files
COPY --from=builder /app/node_modules/.pnpm/db-hafas-stations@2.0.0 ./node_modules/.pnpm/db-hafas-stations@2.0.0

# switch to non-root user
USER node
# expose port
EXPOSE 8169

# start command
CMD ["node", "server.js"]