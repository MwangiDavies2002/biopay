// Keep the API explorer's heading below the page heading in the document outline.
const explorer = document.getElementById('swagger-ui');
const observer = new MutationObserver(() => {
  const title = explorer.querySelector('.info .title');
  if (!title) return;
  observer.disconnect();
  if (title.tagName === 'H1') {
    const heading = document.createElement('h2');
    heading.className = title.className;
    while (title.firstChild) heading.appendChild(title.firstChild);
    title.replaceWith(heading);
  }
});
observer.observe(explorer, {childList: true, subtree: true});
