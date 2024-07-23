package cs446.project.chameleon

import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavHostController
import cs446.project.chameleon.composables.FavouritesBar
import cs446.project.chameleon.composables.HistoryRows
import cs446.project.chameleon.composables.styling.CenteredColumn
import cs446.project.chameleon.composables.styling.ChameleonDivider
import cs446.project.chameleon.composables.styling.ChameleonText
import cs446.project.chameleon.composables.styling.Screen
import cs446.project.chameleon.data.viewmodel.ImageViewModel
import cs446.project.chameleon.data.viewmodel.PaintViewModel
import cs446.project.chameleon.data.viewmodel.UserViewModel
import cs446.project.chameleon.utils.HEADER

@Composable
fun ProfileScreen(
    navController: NavHostController,
    mainViewModel: PaintViewModel = viewModel(),
    userViewModel: UserViewModel = viewModel(),
    imageViewModel: ImageViewModel = viewModel()
) {
    val user = userViewModel.getUser() ?: return
    val favourites by userViewModel.favourites.collectAsState()
    val history by userViewModel.historyList.collectAsState()

    Screen(navController, userViewModel) { padding ->
        CenteredColumn(modifier = Modifier.padding(padding)) {
            // Title
            ChameleonText("${user.firstname} ${user.lastname}", HEADER)
            ChameleonDivider()
            Spacer(modifier = Modifier.height(12.dp))

            FavouritesBar(
                favourites,
                onClick = { paint ->
                    mainViewModel.updateSelectedPaint(paint)
                    navController.navigate("paint_review")
                }
            )

            Spacer(modifier = Modifier.height(100.dp))

            HistoryRows(
                navController,
                history,
                imageViewModel,
                userViewModel
            )
        }
    }
}
