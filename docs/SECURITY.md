# Security and privacy requirements

## Prototype restrictions
- The current HTTP API has no operator authentication. Bind it to localhost only.
- Never expose the prototype through Nginx, public hosting, or a campus network.
- The camera preview/detection utilities are local only; they do not store or transmit images.
- Face detection is **not** recognition or proof of identity.
- The access-policy evaluator is a pure library, not wired into physical gate control.
- The gate simulator cannot operate hardware and requires explicit operator approval.

## Production blockers
- Add SSO/OIDC authentication, RBAC and rate limiting before network deployment.
- Implement signed, auditable approvals and separation of duties.
- Obtain informed consent and offer an equivalent non-biometric access route.
- Define retention, deletion and encrypted storage for biometric data.
- Conduct independent accuracy, false acceptance/rejection, demographic and spoof testing.
- Review local law and university policy.
- Hardware gate integration requires safety review, emergency egress, override, and fail-safe operation.
- Use HTTPS, credential rotation, backups, migrations, and security monitoring.
