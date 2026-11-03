// Compact navy hero band — approved stand-in for the site's photo hero (PLAN §6).
export default function Hero() {
  return (
    <section className="bg-kicmpi-navy">
      <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6">
        <span className="mb-3 inline-block rounded-full bg-kicmpi-magenta px-3 py-1 text-xs font-bold uppercase tracking-wider text-white">
          Concept — RAG prototype
        </span>
        <h1 className="text-3xl font-bold text-white sm:text-4xl">KicMPi Kennisassistent</h1>
        <p className="mt-2 max-w-2xl text-white/80">
          Upload een PDF, volg de RAG-pijplijn live (lezen → chunken → embedden → opgeslagen) en
          stel vragen aan de opgeslagen kennis — met AI-samenvatting en bronvermelding.
        </p>
      </div>
    </section>
  )
}
