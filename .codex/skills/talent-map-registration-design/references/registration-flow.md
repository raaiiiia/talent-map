# Registration Flow

Use this flow for the Talent Map local edition registration screen.

1. User opens the auth screen and chooses the register tab.
2. Required fields are name, email, email verification code, password, password confirmation, and robot detection.
3. Email verification code is sent only after a valid email is present.
4. After a code is sent, the send button enters a 60-second cooldown. The client displays a second-by-second countdown and the server rejects repeat sends inside the same 60-second window.
5. The robot detection challenge is generated before registration and can be refreshed independently.
6. Registration submission includes the hidden challenge id, the four-character challenge answer, and a honeypot field.
7. The server verifies the honeypot, captcha answer, email code, password confirmation, and account uniqueness before creating the account.
8. A newly registered and email-verified account receives one free search trial.

Do not replace server-side cooldown with client-only timing. The button countdown is only the interface state; the server check is the enforcement.
