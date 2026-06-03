# Captcha Design

Source reference:

- Baidu Tashuo page requested by the user: `https://baike.baidu.com/tashuo/browse/content?id=294b5d3c8933402ad5c9cdce`
- If the public page is script-rendered or static scraping exposes no article text, use it only as a reference for mainstream Chinese web verification expectations: familiar, compact, visual, and refreshable.

Implementation standard:

- Use a traditional image captcha, not arithmetic.
- Show exactly four characters.
- Generate the answer server-side from letters and digits, excluding ambiguous characters when possible.
- Render the challenge as an image, preferably an SVG data URI or generated bitmap, and never expose the answer in plaintext JSON.
- Match the visual language of a familiar Chinese web captcha: pale white/greenish background, large green characters, light blur, sparse colored noise dots, one diagonal crossing line, and per-character rotation/skew or vertical offset.
- Store only a challenge id plus answer hash with an expiration time.
- Normalize submitted answers by trimming and uppercasing.
- Refreshing the challenge should replace both the image and hidden challenge id.

Interface pattern:

- Place the captcha image, answer input, and refresh icon in one compact verification row on desktop.
- Use a short placeholder such as "输入图中字符".
- The image should be large enough to read but not dominate the form, around 136 x 48 px.
- On mobile, stack the image, input, and refresh control so text never overflows.
