import useGlobal from "@/assets/core/useGlobal";
import { FontAwesomeIcon } from "@fortawesome/react-native-fontawesome";
import { useNavigation } from "@react-navigation/native";
import React, { useEffect, useLayoutEffect, useState } from "react";
import {
  ActivityIndicator,
  SafeAreaView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import CompleteSignUpTopView from "../TopViews/CompleteSignUpTopView";
import AuthInput from "./AuthInput";

//import { Globals } from "../..//Light";
import { DGlobals } from "@/constants/DarkColor/DGlobals";

// ============= Light ============================//

//import { Globals } from "../..//Light";

import PickerView from "./PickerView";

const CompleteSignUp = () => {
  const navigation = useNavigation();
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [status, setStatus] = useState("");
  const [FirstNameError, setFirstNameError] = useState("");
  const [LastNameError, setLastNameError] = useState("");
  const [statusError, setStatusError] = useState("");

  const { theme } = useGlobal();
  let isLight = theme === "light";

  const user = useGlobal((state) => state.user);
  const logout = useGlobal((state) => state.logout);
  const completeSignUpDetails = useGlobal(
    (state) => state.completeSignUpDetails
  );
  const isLoading = useGlobal((state) => state.appState.isLoading);

  console.log(user.username);

  const [open, setOpen] = useState(false);
  const [value, setValue] = useState(null);
  const [statusItems, setStatusItems] = useState([
    { label: "Student", value: "Student" },
    { label: "Staff", value: "Staff" },
  ]);

  const handleComplete = async () => {
    const failFirstName = !firstName.trim();
    if (failFirstName) {
      setFirstNameError("first name Not Provided");
    }

    const failLastName = !lastName.trim();
    if (failLastName) {
      setLastNameError("last name Not Provided");
    }

    const failStatus = !value;
    setStatus(value);
    if (failStatus) {
      setStatusError("select status");
    }

    if (failFirstName || failLastName || failStatus) {
      return;
    }

    const completedDetails = {
      first_name: firstName.trim(),
      last_name: lastName.trim(),
      directory_status1: value,
    };

    const result = await completeSignUpDetails(completedDetails);

    if (result.success) {
      console.log(`user ${user.username} completed signup details`);
    } else {
      console.warn(
        `user ${user.username} failed to complete signup details:`,
        result.error
      );
    }
  };

  useLayoutEffect(() => {
    navigation.setOptions({
      header: () => <CompleteSignUpTopView user={user} />,
    });
  }, []);

  useEffect(() => {
    user;
  });
  return (
    <SafeAreaView
      style={{
        flex: 1,
        backgroundColor: "#151718",
        paddingTop: "20%",
      }}
    >
      <Text
        style={{
          marginVertical: "2%",
          color: "rgba(159, 159, 159, 0.68)",
          fontWeight: "600",
          textAlign: "center",
        }}
      >
        
      </Text>
      <Text
        style={{
          marginBottom: "5%",
          marginHorizontal:"10%",
          color: "rgba(159, 159, 159, 0.68)",
          fontWeight: "600",
          textAlign: "left",
        }}
      >
        Hie {user.username}, welcome to the community, Enter correct details 
      </Text>

      <View style={{ marginTop: "10%", marginBottom: "5%" }}>
      <AuthInput
        icon={
          <FontAwesomeIcon
            style={{ marginLeft: 8 }}
              icon="fa-solid fa-user"
              size={20}
              color={FirstNameError ? "#ff3636" : "#9BA1A6"}
            />
          }
          value={firstName}
        onChangeText={(text) => {
            setFirstName(text);
            if (FirstNameError) {
              setFirstNameError("");
          }
        }}
          placeholder={
            FirstNameError ? "first name not provided" : "first name"
          }
          placeholderTextColor={FirstNameError ? "#ff3636" : "#9BA1A6"}
          Space={true}
        />

        <AuthInput
        icon={
          <FontAwesomeIcon
              icon="fa-solid fa-user"
              size={20}
              color={LastNameError ? "#ff3636" : "#9BA1A6"}
            style={{ marginLeft: 8 }}
          />
        }
          value={lastName}
        onChangeText={(text) => {
            setLastName(text);
            if (LastNameError) {
              setLastNameError("");
          }
        }}
          placeholder={LastNameError ? "last name not provided" : "last name"}
          placeholderTextColor={LastNameError ? "#ff3636" : "#9BA1A6"}
          Space={true}
          />

        <PickerView
          open={open}
          value={value}
          items={statusItems}
          setOpen={setOpen}
          setValue={setValue}
          setItems={setStatusItems}
        onChangeText={(text) => {
            setValue(text);
            if (statusError) {
              setStatusError("");
          }
        }}
          Space={false}
        icon={
          <FontAwesomeIcon
              icon="fa-solid fa-school"
              size={20}
              color={statusError ? "#ff3636" : "#9BA1A6"}
            style={{ marginLeft: 8 }}
          />
        }
          placeholder={statusError ? "select status" : "select status"}
          placeholderTextColor={statusError ? "#ff3636" : "#9BA1A6"}
          arrowColor={statusError ? "#ff3636" : "#9BA1A6"}
          onPress={logout}
          Forgot_Password={"logout"}
        />
      </View>

      <TouchableOpacity
        activeOpacity={0.5}
        onPress={handleComplete}
        disabled={isLoading}
        style={{
          width: "90%",
          backgroundColor: DGlobals.icon,
          borderBottomLeftRadius: 25,
          borderBottomRightRadius: 25,
          borderTopLeftRadius: 25,
          borderTopRightRadius: 25,
          alignSelf: "center",
          paddingVertical: 15,
          marginVertical: "15%",
        }}
      >
        {isLoading ? (
          <ActivityIndicator color="#FFFFFF" size="small" />
        ) : (
          <Text
            style={{
              color: "#FFFFFF",
              fontWeight: "bold",
              textAlign: "center",
            }}
          >
            Continue
          </Text>
        )}
      </TouchableOpacity>
    </SafeAreaView>
  );
};

export default CompleteSignUp;

const styles = StyleSheet.create({});
