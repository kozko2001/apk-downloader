import com.aurora.gplayapi.helpers.AppDetailsHelper
import com.aurora.gplayapi.helpers.AuthHelper
import com.aurora.gplayapi.helpers.PurchaseHelper
import java.io.InputStream
import java.net.URL
import java.nio.file.Files
import java.nio.file.Paths
import java.nio.file.StandardCopyOption
import kotlin.system.exitProcess


fun main(args: Array<String>) {

    if (args.count() != 3) {
        println("not enough arguments:")
        println("first argument is the mail for authentication")
        println("second argument is the aasToken")
        println("third argument is the packageName")
        exitProcess(1)
    }

    var user = args[0];
    var token = args[1];
    var packageName = args[2];

    val auth = AuthHelper.build(user, token)
    val app = AppDetailsHelper(auth).getAppByPackageName(packageName)


    val files = PurchaseHelper(auth).purchase(
        app.packageName,
        app.versionCode,
        app.offerType
    )

    files.forEach {
        println("${it.name} ${it.url}")

        val `in`: InputStream = URL(it.url).openStream()
        Files.copy(`in`, Paths.get("output/${it.name}"), StandardCopyOption.REPLACE_EXISTING)
    }

}