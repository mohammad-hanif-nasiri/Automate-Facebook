(function () {
  const headerElement = document.querySelector("header");
  const titleElement = headerElement.querySelector(".title");

  titleElement.innerHTML = document.title;

  Array.from(headerElement.querySelectorAll("a")).forEach(
    (elem, index, array) => {
      if (
        elem.href.replace(/(\?|\#.*)/, "") ==
        window.location.href.replace(/(\?|\#.*)/, "")
      ) {
        elem.classList.add("active");
      }
    },
  );
}).call();
