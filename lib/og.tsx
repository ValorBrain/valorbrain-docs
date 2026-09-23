/**
 * OG image Brand V. v2.0.0: obsidian + símbolo oficial + wordmark Hanken 800.
 * O SVG abaixo são os bytes exatos do kit
 * (deliverables/brand-kit/brand_assets/valorbrain-symbol.svg, ADR 0004)
 * embutidos como data URI para o satori do next/og renderizar sem rede.
 */
const SYMBOL_SVG =
  '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 1000" width="100%" height="100%">' +
  '<title>ValorBrain Symbol</title>' +
  '<rect width="1000" height="1000" rx="225" fill="#111317"/>' +
  '<path d="M448.85395478 750.0 245.0 250.00000145999996H397.129817L505.64908646000004 568.45841838L616.19675348 250.00000145999996H766.2981729200001L562.44421814 750.0Z" fill="#FFFFFF"/>' +
  '<circle cx="731" cy="676" r="74" fill="#3F9E5E"/>' +
  '</svg>';

const symbolDataUri = `data:image/svg+xml;base64,${Buffer.from(SYMBOL_SVG).toString('base64')}`;

export function DocsOGImage({
  title,
  description,
  site,
}: {
  title: string;
  description?: string;
  site?: string;
}) {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        width: '100%',
        height: '100%',
        padding: '4rem',
        backgroundColor: '#111317', /* --vb-obsidian (kit v2.0.0) */
        color: '#FFFFFF',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={symbolDataUri} width={64} height={64} alt="" />
        <p
          style={{
            margin: 0,
            fontWeight: 800,
            fontSize: 40,
            letterSpacing: '-0.04em',
          }}
        >
          {site ?? 'ValorBrain'}
        </p>
      </div>
      <p
        style={{
          margin: 0,
          marginTop: 'auto',
          fontWeight: 800,
          fontSize: title.length > 60 ? 64 : 80,
          lineHeight: 1.1,
          letterSpacing: '-0.025em',
        }}
      >
        {title}
      </p>
      {description ? (
        <p
          style={{
            margin: 0,
            marginTop: '20px',
            fontSize: 40,
            lineHeight: 1.3,
            color: '#D8DCD7', /* --vb-neutral-300 */
          }}
        >
          {description}
        </p>
      ) : null}
      <div
        style={{
          display: 'flex',
          marginTop: '32px',
          paddingBottom: '10px',
          borderBottom: '6px solid #3F9E5E', /* --vb-green: acento da marca */
        }}
      >
        <p style={{ margin: 0, fontSize: 32, color: '#8FD0A5' /* green-300 p/ AA no obsidian */ }}>
          docs.valor.digital
        </p>
      </div>
    </div>
  );
}
