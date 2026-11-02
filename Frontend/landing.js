
(function () {
    const $ = s => document.querySelector(s);

    const hero = $('#top');
    const dash = $('#dash');
    const nav = $('#nav');

    // Stop if the landing page is not present
    if (!hero || !dash || !nav) return;

    function sc() {
        nav.classList.toggle('s', window.scrollY > 30);
        dash.style.setProperty(
            '--rx',
            10 * Math.max(0, 1 - window.scrollY / 460) + 'deg'
        );
    }

    window.addEventListener('scroll', sc, { passive: true });
    sc();

    // Reveal animations
    const io = new IntersectionObserver(entries => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('in');
                io.unobserve(entry.target);
            }
        });
    }, { threshold: 0.2 });

    document.querySelectorAll('.rv').forEach(el => io.observe(el));

    // Number counter animation
    function count(el, delay = 0) {
        const to = +el.dataset.n;
        const prefix = el.dataset.pre || '';
        const start = performance.now() + delay;

        function animate(time) {
            const k = Math.min(Math.max((time - start) / 1600, 0), 1);
            const eased = 1 - Math.pow(1 - k, 4);

            el.textContent =
                prefix + Math.round(to * eased).toLocaleString('en-IN');

            if (k < 1) requestAnimationFrame(animate);
        }

        requestAnimationFrame(animate);
    }

    const counterObserver = new IntersectionObserver(entries => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                count(entry.target);
                counterObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.6 });

    document.querySelectorAll('[data-n]').forEach(el => {
        if (el.closest('.hero')) {
            count(el, 1100);
        } else {
            counterObserver.observe(el);
        }
    });

    // Hero mouse movement effect
    if (window.matchMedia('(hover:hover)').matches) {
        hero.addEventListener('mousemove', e => {
            const r = hero.getBoundingClientRect();
            const x = (e.clientX - r.left) / r.width;
            const y = (e.clientY - r.top) / r.height;

            hero.style.setProperty('--mx', x * 100 + '%');
            hero.style.setProperty('--my', y * 100 + '%');
            hero.style.setProperty('--px', (x - 0.5) * 2);
            hero.style.setProperty('--py', (y - 0.5) * 2);
        });
    }

    // How it works steps
    const steps = [...document.querySelectorAll('.step')];
    const scenes = [...document.querySelectorAll('.scene')];

    if (steps.length && scenes.length) {
        const stepObserver = new IntersectionObserver(entries => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const i = +entry.target.dataset.i;

                    steps.forEach((s, j) =>
                        s.classList.toggle('on', j === i)
                    );

                    scenes.forEach((s, j) =>
                        s.classList.toggle('on', j === i)
                    );
                }
            });
        }, { rootMargin: '-45% 0px -45% 0px' });

        steps.forEach(step => stepObserver.observe(step));
    }

    // Before and after comparison slider
    const ba = $('#ba');
    const rg = $('#rg');

    if (ba && rg) {
        rg.addEventListener('input', () => {
            ba.style.setProperty('--p', rg.value + '%');
        });

        new IntersectionObserver((entries, observer) => {
            if (entries[0].isIntersecting) {
                observer.disconnect();

                const start = performance.now();

                function animate(time) {
                    const k = Math.min((time - start) / 1700, 1);
                    const value = 96 - 46 * (1 - Math.pow(1 - k, 3));

                    ba.style.setProperty('--p', value + '%');
                    rg.value = value;

                    if (k < 1) requestAnimationFrame(animate);
                }

                requestAnimationFrame(animate);
            }
        }, { threshold: 0.55 }).observe(ba);
    }

    // Interactive stock demo
    const products = [
        ['Pendrive 64GB', 75, 20],
        ['Keyboard', 25, 20],
        ['Wireless mouse', 48, 20]
    ];

    const maxStock = 100;
    const demoList = $('#dml');
    const toast = $('#ts');
    let toastTimer;

    if (demoList && toast) {
        demoList.innerHTML = products.map((product, i) => `
            <div class="sr" data-i="${i}">
                <span class="nm">
                    ${product[0]}
                    <small class="rc">Reorder soon</small>
                </span>
                <em></em>
                <span>
                    <button class="sb" data-d="-5">−5</button>
                    <button class="sb" data-d="10">+10</button>
                </span>
                <div class="pbar"><i></i></div>
            </div>
        `).join('');

        function drawStock(i) {
            const product = products[i];
            const row = demoList.children[i];

            row.style.setProperty(
                '--w',
                product[1] / maxStock * 100 + '%'
            );

            row.querySelector('em').textContent = product[1];
            row.classList.toggle('low', product[1] <= product[2]);
        }

        products.forEach((_, i) => drawStock(i));

        demoList.addEventListener('click', e => {
            const button = e.target.closest('button');
            if (!button) return;

            const row = button.closest('.sr');
            const i = +row.dataset.i;
            const product = products[i];
            const wasLow = product[1] <= product[2];

            product[1] = Math.max(
                0,
                Math.min(maxStock, product[1] + Number(button.dataset.d))
            );

            drawStock(i);

            if (!wasLow && product[1] <= product[2]) {
                toast.textContent =
                    'Low stock: ' + product[0] +
                    ' is down to ' + product[1] + ' units';

                toast.classList.add('on');
                clearTimeout(toastTimer);

                toastTimer = setTimeout(() => {
                    toast.classList.remove('on');
                }, 2800);
            }
        });
    }

    // FAQ accordion
    document.querySelectorAll('.qb').forEach(button => {
        button.addEventListener('click', () => {
            const isOpen = button.parentElement.classList.toggle('on');
            button.setAttribute('aria-expanded', isOpen);
        });
    });

})();
