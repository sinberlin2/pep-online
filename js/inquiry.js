(function () {
  var form = document.getElementById("inquiry-form");
  if (!form) return;

  var messageEl = document.getElementById("form-message");
  var endpoint =
    (window.PEP_CONFIG && window.PEP_CONFIG.FORM_ENDPOINT) || "";

  function showMessage(text, type) {
    if (!messageEl) return;
    messageEl.textContent = text;
    messageEl.className = "form-message visible " + type;
  }

  function saveLocal(payload) {
    try {
      var key = "pep_inquiries";
      var list = JSON.parse(localStorage.getItem(key) || "[]");
      list.push(
        Object.assign({ at: new Date().toISOString() }, payload)
      );
      localStorage.setItem(key, JSON.stringify(list));
      return true;
    } catch (e) {
      return false;
    }
  }

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    messageEl.className = "form-message";

    var name = form.name.value.trim();
    var email = form.email.value.trim();
    var venue = form.venue.value.trim();
    var interest = form.interest.value;
    var message = form.message.value.trim();

    if (!name || !email) {
      showMessage("Please enter your name and email.", "error");
      return;
    }

  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      showMessage("Please enter a valid email address.", "error");
      return;
    }

    var payload = {
      name: name,
      email: email,
      venue: venue || "(not provided)",
      interest: interest,
      message: message || "(no message)",
      _subject: "PEP pilot enquiry from " + (venue || name),
    };

    var submitBtn = form.querySelector('button[type="submit"]');
    submitBtn.disabled = true;

    if (endpoint) {
      fetch(endpoint, {
        method: "POST",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      })
        .then(function (res) {
          if (res.ok) {
            form.reset();
            showMessage(
              "Thanks! We received your enquiry and will be in touch soon.",
              "success"
            );
          } else {
            throw new Error("Request failed");
          }
        })
        .catch(function () {
          showMessage(
            "Something went wrong sending your message. Please try again or email us directly.",
            "error"
          );
        })
        .finally(function () {
          submitBtn.disabled = false;
        });
      return;
    }

    saveLocal(payload);
    form.reset();
    showMessage(
      "Thanks! Your enquiry was recorded. Connect Formspree in js/config.js to receive emails.",
      "success"
    );
    submitBtn.disabled = false;
  });
})();
