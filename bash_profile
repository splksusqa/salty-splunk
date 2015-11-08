
function test-call {
    sudo salt-call saltutil.sync_all > /dev/null 2>&1;
    sudo salt-call $1;
}