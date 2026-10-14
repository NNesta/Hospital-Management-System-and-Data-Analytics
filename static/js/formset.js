/*
 * Inline formsets ("one form, many rows"): the "Add row" button clones the
 * <template> holding the empty form and bumps TOTAL_FORMS.
 */
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-formset-add]").forEach((button) => {
    const prefix = button.dataset.formsetAdd;
    const table = document.querySelector(`table[data-formset-prefix="${prefix}"] tbody`);
    const template = document.getElementById(`${prefix}-empty-row`);
    const total = document.getElementById(`id_${prefix}-TOTAL_FORMS`);
    const max = document.getElementById(`id_${prefix}-MAX_NUM_FORMS`);

    button.addEventListener("click", () => {
      const index = parseInt(total.value, 10);
      if (max && index >= parseInt(max.value, 10)) return;
      const html = template.innerHTML.replace(/__prefix__/g, String(index));
      table.insertAdjacentHTML("beforeend", html);
      total.value = String(index + 1);
      table.lastElementChild.querySelector("select, input")?.focus();
    });
  });
});
