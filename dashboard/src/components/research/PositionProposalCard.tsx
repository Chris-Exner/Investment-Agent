import type { PositionProposal } from '../../types'

interface Props {
  proposal: PositionProposal
  onConfirm: (proposal: PositionProposal) => void
}

export default function PositionProposalCard({ proposal, onConfirm }: Props) {
  return (
    <div className="data-card data-card-proposal">
      <div className="data-card-header">
        <span className="data-card-icon">🎯</span>
        <span className="data-card-title">Investment-Vorschlag</span>
      </div>

      <div className="proposal-header">
        <span className="proposal-ticker">{proposal.ticker}</span>
        <span className="proposal-name">{proposal.name}</span>
      </div>

      <div className="proposal-section">
        <div className="proposal-label">Investment-These</div>
        <p className="proposal-text">{proposal.thesis}</p>
      </div>

      <div className="proposal-section">
        <div className="proposal-label">Bear-Case Trigger</div>
        <ul className="proposal-triggers">
          {proposal.bear_triggers.map((t, i) => (
            <li key={i}>{t}</li>
          ))}
        </ul>
      </div>

      <div className="proposal-section">
        <div className="proposal-label">Begründung</div>
        <p className="proposal-text proposal-reasoning">{proposal.reasoning}</p>
      </div>

      <div className="proposal-actions">
        <button className="btn btn-primary" onClick={() => onConfirm(proposal)}>
          Position erstellen
        </button>
      </div>
    </div>
  )
}
