// 기록과 안내를 담는 카드 모양 상자.
export default function Card({ title, children }) {
  return (
    <section className="card">
      {title && <h2 className="card-title">{title}</h2>}
      {children}
    </section>
  )
}
