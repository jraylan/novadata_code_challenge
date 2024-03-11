$(function(){
    const $messageContainer = $('#message-container')

    const TYPES = {
        primary: "primary",
        secondary: "secondary",
        success: "success",
        danger: "danger",
        error: "danger",
        warning: "warning",
        info: "info",
        light: "light",
        debug: "light",
        dark: "dark"
    }

    const DEFAULT_PROPS = {
        message: "",
        type: "info",
        timeout: 5000
    }

    document.createMessage = function(props={}){
        const _props = {
            ...DEFAULT_PROPS,
            ...props
        }

        const _timeout = Math.min(
            Math.max(1000,  parseInt(`${_props.timeout}`) || 5000),
            10000);
            
        const _type = TYPES[_props.type] || 'info'
        const _message = `${_props.message || ''}`
        const _title = `${props.title || ''}`

        const _element = document.createElement('div');
        _element.classList.add('alert')
        _element.classList.add(`alert-${_type}`)
        _element.style.display = 'none'
        _element.setAttribute('role', 'alert')

        if (_title){
            const _title_element = document.createElement('h4');
            _title_element.classList.add('alert-heading')
            _title_element.innerText = _title;
            _element.appendChild(_title_element)
        }
        _element.innerHTML += _message

        $messageContainer.append(_element)


        const dispose = ()=>{
            $(_element).fadeOut(500, function () {
                _element.remove();
            });
        }

        const timeoutId = setTimeout(dispose, _timeout + 500)

        $(_element).fadeIn(500);
        $(_element).on('mouseenter', function(){clearTimeout(timeoutId)});
        $(_element).on('mouseleave', dispose)
    }
})