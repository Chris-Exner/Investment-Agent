import type { DataCard, PositionProposal } from '../../types'
import DataCardStock from './DataCardStock'
import PositionProposalCard from './PositionProposalCard'

interface Props {
  card: DataCard
  onConfirmPosition?: (proposal: PositionProposal) => void
}

export default function DataCardRenderer({ card, onConfirmPosition }: Props) {
  switch (card.type) {
    case 'stock_quote':
      return <DataCardStock data={card.data as Record<string, unknown>} />

    case 'company_financials':
      return <DataCardFinancials data={card.data as Record<string, unknown>} />

    case 'multiple_stocks':
      return <DataCardMultipleStocks data={card.data as Record<string, unknown>[]} />

    case 'sector_performance':
      return <DataCardSectors data={card.data as Record<string, unknown>[]} />

    case 'news':
      return <DataCardNews data={card.data as Record<string, unknown>[]} />

    case 'macro_indicators':
      return <DataCardMacro data={card.data as Record<string, unknown>[]} />

    case 'position_proposal':
      if (onConfirmPosition && card.data) {
        const proposal = card.data as unknown as PositionProposal
        return <PositionProposalCard proposal={proposal} onConfirm={onConfirmPosition} />
      }
      return null

    default:
      return null
  }
}


function DataCardFinancials({ data }: { data: Record<string, unknown> }) {
  const fmt = (v: unknown) => {
    if (v === null || v === undefined) return '—'
    if (typeof v === 'number') {
      if (Math.abs(v) >= 1e9) return `$${(v / 1e9).toFixed(1)}B`
      if (Math.abs(v) >= 1e6) return `$${(v / 1e6).toFixed(0)}M`
      if (Math.abs(v) < 1 && v !== 0) return `${(v * 100).toFixed(1)}%`
      return v.toFixed(2)
    }
    return String(v)
  }

  return (
    <div className="data-card data-card-financials">
      <div className="data-card-header">
        <span className="data-card-icon">📊</span>
        <span className="data-card-title">Fundamentaldaten {String(data.ticker || '')}</span>
      </div>
      <div className="data-card-grid">
        <div className="data-card-item">
          <span className="data-card-label">Umsatz</span>
          <span className="data-card-value">{fmt(data.revenue)}</span>
        </div>
        <div className="data-card-item">
          <span className="data-card-label">Wachstum</span>
          <span className="data-card-value">{fmt(data.revenue_growth)}</span>
        </div>
        <div className="data-card-item">
          <span className="data-card-label">EPS</span>
          <span className="data-card-value">{data.eps != null ? `$${Number(data.eps).toFixed(2)}` : '—'}</span>
        </div>
        <div className="data-card-item">
          <span className="data-card-label">Netto-Marge</span>
          <span className="data-card-value">{fmt(data.net_margin)}</span>
        </div>
        <div className="data-card-item">
          <span className="data-card-label">Free Cash Flow</span>
          <span className="data-card-value">{fmt(data.free_cash_flow)}</span>
        </div>
        <div className="data-card-item">
          <span className="data-card-label">KGV</span>
          <span className="data-card-value">{data.pe_ratio != null ? Number(data.pe_ratio).toFixed(1) : '—'}</span>
        </div>
        <div className="data-card-item">
          <span className="data-card-label">EV/EBITDA</span>
          <span className="data-card-value">{data.ev_ebitda != null ? Number(data.ev_ebitda).toFixed(1) : '—'}</span>
        </div>
        <div className="data-card-item">
          <span className="data-card-label">Beta</span>
          <span className="data-card-value">{data.beta != null ? Number(data.beta).toFixed(2) : '—'}</span>
        </div>
      </div>
    </div>
  )
}


function DataCardMultipleStocks({ data }: { data: Record<string, unknown>[] }) {
  return (
    <div className="data-card">
      <div className="data-card-header">
        <span className="data-card-icon">📈</span>
        <span className="data-card-title">Aktienvergleich ({data.length} Titel)</span>
      </div>
      <div className="data-card-table">
        <table>
          <thead>
            <tr>
              <th>Ticker</th>
              <th>Kurs</th>
              <th>Veränderung</th>
              <th>MKap</th>
              <th>KGV</th>
            </tr>
          </thead>
          <tbody>
            {data.map((s, i) => (
              <tr key={i}>
                <td className="data-card-ticker">{String(s.ticker || '')}</td>
                <td>${Number(s.price || 0).toFixed(2)}</td>
                <td className={Number(s.change_pct || 0) >= 0 ? 'text-success' : 'text-danger'}>
                  {Number(s.change_pct || 0) >= 0 ? '+' : ''}{Number(s.change_pct || 0).toFixed(2)}%
                </td>
                <td>{s.market_cap ? `$${(Number(s.market_cap) / 1e9).toFixed(0)}B` : '—'}</td>
                <td>{s.pe_ratio ? Number(s.pe_ratio).toFixed(1) : '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}


function DataCardSectors({ data }: { data: Record<string, unknown>[] }) {
  const sorted = [...data].sort((a, b) => Number(b.change_pct || 0) - Number(a.change_pct || 0))
  return (
    <div className="data-card">
      <div className="data-card-header">
        <span className="data-card-icon">🏭</span>
        <span className="data-card-title">Sektorperformance</span>
      </div>
      <div className="data-card-sectors">
        {sorted.map((s, i) => {
          const pct = Number(s.change_pct || 0)
          return (
            <div key={i} className="sector-row">
              <span className="sector-name">{String(s.sector || '')}</span>
              <span className={`sector-pct ${pct >= 0 ? 'text-success' : 'text-danger'}`}>
                {pct >= 0 ? '+' : ''}{pct.toFixed(2)}%
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}


function DataCardNews({ data }: { data: Record<string, unknown>[] }) {
  return (
    <div className="data-card">
      <div className="data-card-header">
        <span className="data-card-icon">📰</span>
        <span className="data-card-title">Nachrichten ({data.length})</span>
      </div>
      <ul className="data-card-news-list">
        {data.slice(0, 8).map((n, i) => (
          <li key={i} className="news-item">
            <span className="news-source">{String(n.source || '')}</span>
            <span className="news-title">{String(n.title || '')}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}


function DataCardMacro({ data }: { data: Record<string, unknown>[] }) {
  return (
    <div className="data-card">
      <div className="data-card-header">
        <span className="data-card-icon">🌍</span>
        <span className="data-card-title">Makro-Indikatoren</span>
      </div>
      <div className="data-card-grid">
        {data.map((ind, i) => (
          <div key={i} className="data-card-item">
            <span className="data-card-label">{String(ind.name || '')}</span>
            <span className="data-card-value">{Number(ind.value || 0).toFixed(2)}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
