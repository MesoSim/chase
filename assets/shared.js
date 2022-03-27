/* Shared JS functions across pages in the chase applet */
/* jQuery must be loaded first */

function loadPlacefileLinks(chase_base_url, api_base) {
    // Update all!
    // TODO: allow for warnings and level 2 to be located elsewhere, not as subdirectory
    //       that probably means loading these data from API, but oh well.
    var team_id = localStorage.getItem("team_id");

    $("#l2-source").val(chase_base_url + "/l2/");
    $("#warnings-source").val(chase_base_url + "/warnings/");
    $("#lsr-placefile").val(chase_base_url + "/" + api_base + "placefile/lsr/content");
    $("#team-current").val(chase_base_url + "/" + api_base + "placefile/team/" + team_id + "/current/content");
    $("#team-tracks").val(chase_base_url + "/" + api_base + "placefile/team/" + team_id + "/tracks/content");
    $("#team-history").val(chase_base_url + "/" + api_base + "placefile/team/" + team_id + "/history/content");
    $("#all-current").val(chase_base_url + "/" + api_base + "placefile/team/current/content");
    $("#all-tracks").val(chase_base_url + "/" + api_base + "placefile/team/tracks/content");
    $("#all-history").val(chase_base_url + "/" + api_base + "placefile/team/history/content");
}
