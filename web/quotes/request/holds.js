/** Summarise quote holds from the committed run snapshot.
 *
 * What: displays held quote quantities without counting them as confirmed seats.
 * When called: the Quotes capability renders or refreshes its market summary.
 * Why: a temporary capacity hold is not a transport reservation.
 */
export function renderQuoteHoldSummary(snapshot) {
  const section = document.createElement("section");
  section.setAttribute("aria-labelledby", "quote-holds-heading");
  const heading = document.createElement("h3");
  heading.id = "quote-holds-heading";
  heading.textContent = "Held capacity";
  section.append(heading);
  const quotes = snapshot?.market?.quotes ?? [];
  const held = quotes.filter((quote) => quote.status === "held");
  const list = document.createElement("ul");
  if (held.length === 0) {
    const empty = document.createElement("li");
    empty.textContent = "No held quotes";
    list.append(empty);
  }
  for (const quote of held) {
    const item = document.createElement("li");
    item.textContent = `${quote.offer_id}: ${quote.offered_seats} seats held until ${quote.expires_at}`;
    list.append(item);
  }
  section.append(list);
  return section;
}
