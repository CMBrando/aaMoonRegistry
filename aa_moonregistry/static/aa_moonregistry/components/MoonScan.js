export default {
    template: '#moonscan-component',
    data: function () {
        return {
            moonscan_text: '',
            moonscan_result: [],
            is_saving: false
        };
    },
    mounted: function () {
        this.$refs.scan_text.focus();
    },
    watch: {

    },
    methods: {
        onPaste: function() {
            this.moonscan_result = parseMoonScan(this.moonscan_text);
        },
        addMoonDetail: function() {
            if (this.is_saving) return;
            if (!this.moonscan_result.length) {
                this.saveToast('error', 'No moon scans were parsed. Paste a scan before saving.');
                return;
            }

            var token = this.$root.$data.token;
            var header = this.$root.$data.header;
            var ajaxHeaders = {};
            ajaxHeaders[header] = token;

            this.is_saving = true;
            $.ajax({
                cache: false,
                type: 'POST',
                url: "SaveMoonDetail",
                data: JSON.stringify(this.moonscan_result),
                contentType: 'application/json; charset=UTF-8',
                processData: false,
                dataType: "json",
                headers: ajaxHeaders
            }).done((data) => {
                const processed = Number(data.processed) || 0;
                if (data.success === true) {
                    this.saveToast('success', 'Saved scans for ' + processed + ' moon' + (processed === 1 ? '' : 's') + '.');
                    this.$emit('scan-added', true);
                } else {
                    const summary = this.saveErrorSummary(data.errors);
                    this.saveToast(processed ? 'warning' : 'error',
                        (processed ? 'Saved scans for ' + processed + ' moon(s), but ' : 'Could not save moon scans. ') + summary);
                    if (processed) this.$emit('scan-added', false);
                }
            }).fail((xhr) => {
                const errors = xhr.responseJSON && xhr.responseJSON.errors;
                const message = errors && errors.length
                    ? this.saveErrorSummary(errors)
                    : 'Could not save moon scans' + (xhr.status ? ' (HTTP ' + xhr.status + ')' : '') + '. Please try again.';
                this.saveToast('error', message);
            }).always(() => {
                this.is_saving = false;
            });
        },
        saveErrorSummary: function(errors) {
            if (!Array.isArray(errors) || !errors.length) return 'The server did not confirm the save.';
            const first = errors[0];
            return errors.length + ' invalid row(s). Row ' + (Number(first.index) + 1) + ': ' + first.error;
        },
        saveToast: function(type, message) {
            toastr[type]($('<div>').text(message).html());
        }
    }
}
