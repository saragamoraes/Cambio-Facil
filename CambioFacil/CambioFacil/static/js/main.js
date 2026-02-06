document.addEventListener('DOMContentLoaded', function () {

    const selectWrappers = document.querySelectorAll('.custom-select-wrapper');

    const swapButton = document.querySelector('.swap-icon-container');

    if (selectWrappers.length < 2 || !swapButton) return;

    const fromWrapper = selectWrappers[0];
    const toWrapper = selectWrappers[1];

    selectWrappers.forEach(wrapper => {

        const display = wrapper.querySelector('.custom-select-display');
        const optionsList = wrapper.querySelector('.custom-options-list');

        let hiddenInput;

        if (wrapper === fromWrapper) hiddenInput = document.getElementById("selected-from-currency");
        else hiddenInput = document.getElementById("selected-to-currency");

        display.addEventListener('click', function () {

            document.querySelectorAll('.custom-select-wrapper.open').forEach(open => {
                if (open !== wrapper) open.classList.remove('open');
            });

            wrapper.classList.toggle('open');
        });

        optionsList.querySelectorAll('.custom-option').forEach(option => {

            option.addEventListener('click', function () {

                const selectedValue = option.dataset.value;
                const selectedImg = option.dataset.img;
                const selectedCode = option.querySelector('.currency-code').textContent;

                display.querySelector('.flag-icon').src =
                    `/static/images/${selectedImg}.png`;

                display.querySelector('.currency-code').textContent = selectedCode;

                hiddenInput.value = selectedValue;

                wrapper.classList.remove('open');
            });
        });

        document.addEventListener('click', function (e) {
            if (!wrapper.contains(e.target)) {
                wrapper.classList.remove('open');
            }
        });

    });

    swapButton.addEventListener('click', function () {

        const fromDisplay = fromWrapper.querySelector('.custom-select-display');
        const toDisplay = toWrapper.querySelector('.custom-select-display');

        const fromHidden = document.getElementById('selected-from-currency');
        const toHidden = document.getElementById('selected-to-currency');

        if (!fromDisplay || !toDisplay || !fromHidden || !toHidden) {
            console.error("Erro: elementos do swap não encontrados.");
            return;
        }

        const temp = {
            value: fromHidden.value,
            code: fromDisplay.querySelector('.currency-code').textContent,
            img: fromDisplay.querySelector('.flag-icon').src
        };

        fromHidden.value = toHidden.value;
        fromDisplay.querySelector('.currency-code').textContent =
            toDisplay.querySelector('.currency-code').textContent;
        fromDisplay.querySelector('.flag-icon').src =
            toDisplay.querySelector('.flag-icon').src;

        toHidden.value = temp.value;
        toDisplay.querySelector('.currency-code').textContent = temp.code;
        toDisplay.querySelector('.flag-icon').src = temp.img;

        swapButton.classList.add('swap-animate');
        setTimeout(() => swapButton.classList.remove('swap-animate'), 500);
    });

});