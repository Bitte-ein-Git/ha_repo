### Deprecated Features

- We have deprecated the `--sslcert` and `--sslkey` CLI options in favor of the `--tlscert` and `--tlskey` options respectively, and will be removing the `--sslcert` and `--sslkey` options in a future release.


### Changes

- Fixed an issue where Standard Users could not join a container to a network
- Fixed an issue where the database encryption secret was incorrectly set
- Fixed an issue with Kubernetes Access Control
- Fixed an issue where GitOps webhook URLs could be reused
- Improved Helm repository validation to align with the behavior of the CLI
- Fixed an issue where the environment status filter did not properly handle the "Failed" state when used with Edge Stacks
- Fixed an issue where registry list API was returning back passwords
- Fixed a data race issue caused by the Kubernetes client
- Fixed an issue where the GitOps interval could be set to less than one minute
- Fixed an issue where CSP blocks Google reCAPTCHA on "Get a Trial License Key" form
- Bumped the following NPM dependencies to resolve vulnerabilities
    - axios → 1.7
    - coverage-v8 → ~2.1.9
    - vitest → 2.1.9
- Resolved the following CVEs
    - CVE-2025-4676
    - CVE-2025-47907

