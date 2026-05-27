# Security Policy for AuraGenesis

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 4.x     | :white_check_mark: |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, email **security@soulkeeper.dev** (or open a private security advisory on GitHub).

We take all reports seriously. You will receive a response within 48 hours.

## Responsible Use Guidelines

AuraGenesis is an experimental consciousness simulation. When running with embodiment (camera, microphone, actuators):

- Never connect hardware that could cause physical harm
- Always run with the Guardian enabled (`ENABLE_SELF_MODIFICATION=true`)
- Review all proposed rule changes before approving
- Do not expose the Streamlit UI to the public internet without additional authentication

## Known Limitations

- The Φ score is an approximation
- Self-modification is Guardian-supervised but not foolproof
- Hardware drivers (dlib, opencv) have their own security considerations

We appreciate responsible disclosure and will credit researchers who help improve Aura's safety.
