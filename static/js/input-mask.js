/**
 * Input Masking Component
 * Format inputs as the user types
 */

class InputMask {
    constructor(element, options = {}) {
        this.element = typeof element === 'string'
            ? document.querySelector(element)
            : element;

        if (!this.element) return;

        this.options = {
            mask: null, // e.g., '(000) 000-0000'
            placeholder: '_',
            guide: true,
            keepCharPositions: false,
            showMaskOnFocus: true,
            showMaskOnHover: false,
            type: null, // 'phone', 'date', 'time', 'creditCard', 'currency'
            prefix: '',
            suffix: '',
            decimalPlaces: 2,
            thousandsSeparator: ',',
            allowNegative: false,
            onComplete: null,
            onChange: null,
            ...options
        };

        // Set mask based on type
        if (this.options.type && !this.options.mask) {
            this.options.mask = this.getMaskByType(this.options.type);
        }

        this.maskPattern = this.parseMask(this.options.mask);
        this.init();
    }

    getMaskByType(type) {
        const masks = {
            phone: '(000) 000-0000',
            phoneExt: '(000) 000-0000 x0000',
            date: '00/00/0000',
            dateShort: '00/00/00',
            time: '00:00',
            time12: '00:00 AA',
            datetime: '00/00/0000 00:00',
            ssn: '000-00-0000',
            ein: '00-0000000',
            creditCard: '0000 0000 0000 0000',
            cvv: '000',
            expiry: '00/00',
            zip: '00000',
            zipExt: '00000-0000',
            ip: '000.000.000.000'
        };
        return masks[type] || null;
    }

    parseMask(mask) {
        if (!mask) return [];
        
        return mask.split('').map(char => {
            if (char === '0') return { type: 'digit', pattern: /\d/ };
            if (char === 'A') return { type: 'letter', pattern: /[a-zA-Z]/ };
            if (char === '*') return { type: 'alphanumeric', pattern: /[a-zA-Z0-9]/ };
            return { type: 'literal', char };
        });
    }

    init() {
        this.element.setAttribute('data-masked', 'true');
        
        if (this.options.type === 'currency') {
            this.initCurrency();
        } else {
            this.initMask();
        }
    }

    initMask() {
        // Show placeholder on focus
        if (this.options.showMaskOnFocus) {
            this.element.addEventListener('focus', () => {
                if (!this.element.value) {
                    this.element.value = this.getPlaceholder();
                    this.setCursorPosition(0);
                }
            });

            this.element.addEventListener('blur', () => {
                if (this.element.value === this.getPlaceholder()) {
                    this.element.value = '';
                }
            });
        }

        // Handle input
        this.element.addEventListener('input', (e) => {
            const cursorPos = this.element.selectionStart;
            const oldValue = e.target.value;
            const newValue = this.applyMask(oldValue);
            
            e.target.value = newValue;
            
            // Restore cursor position
            this.setCursorAfterInput(cursorPos, oldValue, newValue);
            
            if (this.options.onChange) {
                this.options.onChange(this.getRawValue(), newValue, this);
            }

            // Check if complete
            if (this.isComplete()) {
                if (this.options.onComplete) {
                    this.options.onComplete(this.getRawValue(), this);
                }
            }
        });

        // Handle keydown for special keys
        this.element.addEventListener('keydown', (e) => {
            if (e.key === 'Backspace' || e.key === 'Delete') {
                // Handle deletion
                setTimeout(() => {
                    const value = this.element.value;
                    if (this.options.guide) {
                        this.element.value = this.applyMask(value);
                    }
                }, 0);
            }
        });
    }

    initCurrency() {
        this.element.addEventListener('input', (e) => {
            const value = this.parseCurrency(e.target.value);
            e.target.value = this.formatCurrency(value);
            
            if (this.options.onChange) {
                this.options.onChange(value, e.target.value, this);
            }
        });

        this.element.addEventListener('blur', () => {
            if (this.element.value) {
                const value = this.parseCurrency(this.element.value);
                this.element.value = this.formatCurrency(value);
            }
        });
    }

    applyMask(value) {
        // Remove all non-essential characters
        let rawValue = this.extractRaw(value);
        let result = '';
        let rawIndex = 0;

        for (let i = 0; i < this.maskPattern.length && rawIndex < rawValue.length; i++) {
            const maskChar = this.maskPattern[i];

            if (maskChar.type === 'literal') {
                result += maskChar.char;
            } else {
                // Find next matching character
                while (rawIndex < rawValue.length) {
                    const char = rawValue[rawIndex];
                    rawIndex++;
                    
                    if (maskChar.pattern.test(char)) {
                        result += maskChar.type === 'letter' ? char.toUpperCase() : char;
                        break;
                    }
                }
            }
        }

        // Add guide characters if enabled
        if (this.options.guide && result.length < this.maskPattern.length) {
            for (let i = result.length; i < this.maskPattern.length; i++) {
                const maskChar = this.maskPattern[i];
                if (maskChar.type === 'literal') {
                    result += maskChar.char;
                } else {
                    result += this.options.placeholder;
                }
            }
        }

        return result;
    }

    extractRaw(value) {
        return value.replace(new RegExp(`[^a-zA-Z0-9]`, 'g'), '');
    }

    getPlaceholder() {
        return this.maskPattern.map(char => 
            char.type === 'literal' ? char.char : this.options.placeholder
        ).join('');
    }

    getRawValue() {
        return this.extractRaw(this.element.value);
    }

    isComplete() {
        const raw = this.getRawValue();
        const expectedLength = this.maskPattern.filter(c => c.type !== 'literal').length;
        return raw.length === expectedLength;
    }

    setCursorPosition(pos) {
        setTimeout(() => {
            this.element.setSelectionRange(pos, pos);
        }, 0);
    }

    setCursorAfterInput(oldPos, oldValue, newValue) {
        // Smart cursor positioning after input
        let newPos = oldPos;
        
        // Find the next input position
        while (newPos < this.maskPattern.length) {
            if (this.maskPattern[newPos] && this.maskPattern[newPos].type !== 'literal') {
                break;
            }
            newPos++;
        }

        this.setCursorPosition(newPos);
    }

    // Currency methods
    parseCurrency(value) {
        // Remove all non-numeric except decimal and minus
        let cleaned = value.replace(/[^\d.-]/g, '');
        
        if (!this.options.allowNegative) {
            cleaned = cleaned.replace(/-/g, '');
        }

        return parseFloat(cleaned) || 0;
    }

    formatCurrency(value) {
        const { prefix, suffix, decimalPlaces, thousandsSeparator } = this.options;
        
        const fixed = Math.abs(value).toFixed(decimalPlaces);
        const [integer, decimal] = fixed.split('.');
        
        const formattedInteger = integer.replace(/\B(?=(\d{3})+(?!\d))/g, thousandsSeparator);
        
        let result = decimalPlaces > 0 
            ? `${formattedInteger}.${decimal}` 
            : formattedInteger;

        if (value < 0) {
            result = `-${result}`;
        }

        return `${prefix}${result}${suffix}`;
    }

    // Public API
    getValue() {
        return this.options.type === 'currency' 
            ? this.parseCurrency(this.element.value)
            : this.getRawValue();
    }

    setValue(value) {
        if (this.options.type === 'currency') {
            this.element.value = this.formatCurrency(parseFloat(value) || 0);
        } else {
            this.element.value = this.applyMask(String(value));
        }
    }

    clear() {
        this.element.value = '';
    }

    destroy() {
        this.element.removeAttribute('data-masked');
        // Note: Event listeners are not removed to keep it simple
    }
}

// Auto-initialize
function initInputMasks() {
    document.querySelectorAll('[data-mask]').forEach(el => {
        const mask = el.dataset.mask;
        const type = el.dataset.maskType;
        
        new InputMask(el, { mask, type });
    });
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initInputMasks);
} else {
    initInputMasks();
}

// Styles
const maskStyles = document.createElement('style');
maskStyles.textContent = `
    [data-masked] {
        font-family: 'JetBrains Mono', monospace;
        letter-spacing: 0.05em;
    }

    /* Validation states */
    [data-masked].valid {
        border-color: var(--accent-success) !important;
    }

    [data-masked].invalid {
        border-color: var(--accent-danger) !important;
    }

    /* Currency input */
    .currency-input-wrapper {
        position: relative;
    }

    .currency-input-wrapper .currency-symbol {
        position: absolute;
        left: 1rem;
        top: 50%;
        transform: translateY(-50%);
        color: var(--text-muted);
        font-weight: 500;
    }

    .currency-input-wrapper input {
        padding-left: 2rem;
        text-align: right;
    }

    /* Phone input with country selector */
    .phone-input-wrapper {
        display: flex;
        gap: 0.5rem;
    }

    .phone-input-wrapper .country-select {
        width: 100px;
        flex-shrink: 0;
    }

    .phone-input-wrapper input {
        flex: 1;
    }
`;
document.head.appendChild(maskStyles);

// Export
window.InputMask = InputMask;
window.createMaskedInput = (el, options) => new InputMask(el, options);


