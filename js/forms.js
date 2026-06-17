/**
 * Sign-up forms → Netlify Forms.
 *
 * Handles every `<form data-netlify="true">` on the site (the venue pilot
 * enquiry and the subscriber list). Submissions are AJAX-posted to Netlify so
 * the visitor stays on the page and sees an inline confirmation.
 *
 * Netlify captures these automatically once the site is deployed on Netlify —
 * no API key or endpoint to configure. View/forward them in the Netlify
 * dashboard under **Forms** (set up an email notification there to reach
 * sjdoyle46@gmail.com).
 *
 * Each form needs: name=, method="POST", data-netlify="true", a hidden
 * <input name="form-name"> matching the form name, and a hidden bot-field
 * honeypot. See for-venues.html / index.html.
 */
(function () {
  var forms = document.querySelectorAll('form[data-netlify="true"]');
  if (!forms.length) return;

  // On localhost / file:// previews Netlify can't capture submissions, so we
  // confirm without posting (keeps `npm start` testing friendly).
  var isPreview =
    location.protocol === "file:" ||
    /^(localhost|127\.0\.0\.1|0\.0\.0\.0|\[::1\])$/.test(location.hostname);

  function messageEl(form) {
    return form.querySelector(".form-message");
  }

  function showMessage(form, text, type) {
    var el = messageEl(form);
    if (!el) return;
    el.textContent = text;
    el.className = "form-message visible " + type;
  }

  function encode(data) {
    return Object.keys(data)
      .map(function (key) {
        return encodeURIComponent(key) + "=" + encodeURIComponent(data[key]);
      })
      .join("&");
  }

  Array.prototype.forEach.call(forms, function (form) {
    var successText =
      form.getAttribute("data-success") ||
      "Thanks! You're on the list — we'll be in touch soon.";

    form.addEventListener("submit", function (event) {
      event.preventDefault();

      var el = messageEl(form);
      if (el) el.className = "form-message";

      // Honeypot filled → almost certainly a bot. Pretend success, send nothing.
      var honeypot = form.querySelector('[name="bot-field"]');
      if (honeypot && honeypot.value) {
        form.reset();
        showMessage(form, successText, "success");
        return;
      }

      var nameField = form.querySelector('input[name="name"]');
      var name = nameField ? nameField.value.trim() : "";
      if (nameField && nameField.hasAttribute("required") && !name) {
        showMessage(form, "Please enter your name.", "error");
        return;
      }

      var emailField = form.querySelector('input[type="email"], input[name="email"]');
      var email = emailField ? emailField.value.trim() : "";
      if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        showMessage(form, "Please enter a valid email address.", "error");
        return;
      }

      var data = {};
      new FormData(form).forEach(function (value, key) {
        data[key] = value;
      });
      delete data["bot-field"];

      var submitBtn = form.querySelector('button[type="submit"]');
      if (submitBtn) submitBtn.disabled = true;

      function finish(ok) {
        if (submitBtn) submitBtn.disabled = false;
        if (ok) {
          form.reset();
          showMessage(form, successText, "success");
        } else {
          showMessage(
            form,
            "Something went wrong sending that. Please try again, or email us at sjdoyle46@gmail.com.",
            "error"
          );
        }
      }

      if (isPreview) {
        finish(true);
        return;
      }

      fetch(form.getAttribute("action") || "/", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: encode(data),
      })
        .then(function (res) {
          finish(res.ok);
        })
        .catch(function () {
          finish(false);
        });
    });
  });
})();
