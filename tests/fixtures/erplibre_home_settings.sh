# © 2026 TechnoLibre (http://www.technolibre.ca)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
#
# Test double of ERPLibre's script/install/erplibre_home_settings.sh: the
# two functions the deck program calls, as CONTRACT.md states them. The
# tests source it when the deck runs outside an ERPLibre checkout; inside
# one, they use the real library.
#
# streamdeck.conf is $XDG_CONFIG_HOME/erplibre-home/streamdeck.conf
# (~/.config when unset or empty); the last "KEY=" line of a key wins.

deck_setting() {
    local LC_ALL=C
    local key="$1" value="$2" line
    local file="${XDG_CONFIG_HOME:-${HOME}/.config}/erplibre-home/streamdeck.conf"
    if [ -f "${file}" ]; then
        while IFS= read -r line || [ -n "${line}" ]; do
            case "${line}" in
                "${key}="*) value="${line#*=}" ;;
            esac
        done <"${file}"
    fi
    echo "${value}"
}

# One plugin id per line: DECK_PLUGINS_OFF cut at the commas, every blank
# removed, empty pieces skipped.
deck_plugins_off() {
    local part
    local -a parts
    IFS=',' read -r -a parts <<<"$(deck_setting DECK_PLUGINS_OFF "")"
    for part in "${parts[@]}"; do
        part="${part//[[:space:]]/}"
        [ -n "${part}" ] && echo "${part}"
    done
    return 0
}

# DECK_SESSION_REFRESH_SEC, edge blanks removed, when it is a decimal
# number with a dot from 0.5 to 60; 1 otherwise.
deck_session_refresh_sec() {
    local value
    value="$(deck_setting DECK_SESSION_REFRESH_SEC 1)"
    value="${value#"${value%%[![:space:]]*}"}"
    value="${value%"${value##*[![:space:]]}"}"
    if [[ "${value}" =~ ^([0-9]+\.?[0-9]*|\.[0-9]+)$ ]] &&
        awk -v v="${value}" 'BEGIN { exit !(v >= 0.5 && v <= 60) }'; then
        echo "${value}"
    else
        echo 1
    fi
    return 0
}
