(()=>{
    $(function(){

        const SELECTOR = 'div[contenteditable][data-role="composer-text-field"]'
    

        $(document).on('input paste', SELECTOR, function(e){

            const editor = e.target
            const targetElement = $(editor.dataset.target)

            switch (e.originalEvent?.inputType) {
                case "formatItalic":
                case "formatBold":
                case "formatItalic":
                case "formatUnderline":
                case "formatStrikeThrough":
                case "formatSuperscript":
                case "formatSubscript":
                case "formatJustifyFull":
                case "formatJustifyCenter":
                case "formatJustifyRight":
                case "formatJustifyLeft":
                    editor.innerText = editor.innerText
                    break
                default:
                    break;
            }

            if(e.originalEvent.type == 'paste'){
                e.preventDefault();
                editor.innerText = e.originalEvent.clipboardData.getData('text');
            }

            if (targetElement){
                targetElement.val(editor.innerText)
            }
        })
    })}
)()