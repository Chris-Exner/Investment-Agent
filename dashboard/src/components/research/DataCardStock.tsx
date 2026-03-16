interface Props {
  data: Record<string, unknown>
}

export default function DataCardStock({ data }: Props) {
  const price = Number(data.price || 0)
  const changePct = Number(data.change_pct || 0)
  const marketCap = data.market_cap ? Number(data.market_cap) : null
  const pe = data.pe_ratio ? Number(data.pe_ratio) : null
  const high52 = data.fifty_two_week_high ? Number(data.fifty_two_week_high) : null
  const low52 = data.fifty_two_week_low ? Number(data.fifty_two_week_low) : null
  const volume = data.volume ? Number(data.volume) : null

  const fmtMcap = (v: number) => {
    if (v >= 1e12) return `$${(v / 1e12).toFixed(2)}T`
    if (v >= 1e9) return `$${(v / 1e9).toFixed(1)}B`
    if (v >= 1e6) return `$${(v / 1e6).toFixed(0)}M`
    return `$${v.toFixed(0)}`
  }

  const fmtVol = (v: number) => {
    if (v >= 1e6) return `${(v / 1e6).toFixed(1)}M`
    if (v >= 1e3) return `${(v / 1e3).toFixed(0)}K`
    return v.toString()
  }

  return (
    <div className="data-card data-card-stock">
      <div className="data-card-header">
        <span className="data-card-icon">💹</span>
        <span className="data-card-ticker">{String(data.ticker || '')}</span>
        <span className="data-card-name">{String(data.name || '')}</span>
      </div>
      <div className="data-card-price-row">
        <span className="data-card-price">${price.toFixed(2)}</span>
        <span className={`data-card-change ${changePct >= 0 ? 'text-success' : 'text-danger'}`}>
          {changePct >= 0 ? '+' : ''}{changePct.toFixed(2)}%
        </span>
      </div>
      <div className="data-card-grid">
        <div className="data-card-item">
          <span className="data-card-label">MKap</span>
          <span className="data-card-value">{marketCap ? fmtMcap(marketCap) : '—'}</span>
        </div>
        <div className="data-card-item">
          <span className="data-card-label">KGV</span>
          <span className="data-card-value">{pe ? pe.toFixed(1) : '—'}</span>
        </div>
        <div className="data-card-item">
          <span className="data-card-label">52W Hoch</span>
          <span className="data-card-value">{high52 ? `$${high52.toFixed(2)}` : '—'}</span>
        </div>
        <div className="data-card-item">
          <span className="data-card-label">52W Tief</span>
          <span className="data-card-value">{low52 ? `$${low52.toFixed(2)}` : '—'}</span>
        </div>
        {volume && (
          <div className="data-card-item">
            <span className="data-card-label">Volumen</span>
            <span className="data-card-value">{fmtVol(volume)}</span>
          </div>
        )}
      </div>
    </div>
  )
}
