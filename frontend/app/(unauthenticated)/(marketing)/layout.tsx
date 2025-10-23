// Minimal unauthenticated layout without marketing chrome

export default async function MarketingLayout({
  children
}: {
  children: React.ReactNode
}) {
  return (
    <>{children}</>
  )
}
