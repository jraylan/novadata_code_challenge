(() => {
    document.addEventListener("DOMContentLoaded", () => {
        const forms = document.querySelectorAll('form[data-confirm-message]')

        const DEFAULT_LOCALE = navigator.language
        const DEFAULT_LOCALE_ALT = DEFAULT_LOCALE.split('-')[0]

        forms.forEach(form=>{
            const confirmation_message = form.dataset.confirmMessage

            if (!confirmation_message?.length) return


            // Permitir configuração do locales do bootbox
            const translation = bootbox.locales(DEFAULT_LOCALE) || bootbox.locales(DEFAULT_LOCALE_ALT) || bootbox.locales('pt-BR')


            // Permitir customizar a mensagem de confirmação
            const confirmation_title = form.dataset.confirmTitle
            const confirmation_ok_label = form.dataset.confirmOkLabel || translation.CONFIRM
            const confirmation_cancel_label = form.dataset.confirmCancelLabel || translation.CANCEL
            const confirmation_ok_class_name = form.dataset.confirmOkClassName || 'btn-danger'
            const confirmation_cancel_class_name = form.dataset.confirmCancelClassName || 'btn-primary'

            form.addEventListener('submit', (e)=>{
                e.preventDefault();
                e.stopPropagation();

                bootbox.confirm({
                    title: confirmation_title,
                    message: confirmation_message,
                    buttons:{
                        confirm: {
                            label: confirmation_ok_label,
                            className: confirmation_ok_class_name
                        },
                        cancel: {
                            label: confirmation_cancel_label,
                            className: confirmation_cancel_class_name
                        }
                    },
                    callback: (ok)=>{
                        if (ok) form.submit();
                    }
                })
            });
        })
    })
})()